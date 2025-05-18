import atexit  
import multiprocessing  
import uuid  
import asyncio  
import base64  
import html2text  
  
from browser_use.browser.browser import Browser, BrowserConfig  
from browser_use.browser.context import BrowserContextConfig  
  
class BrowserUseEnv:  
    def __init__(self):  
        # HTML转文本转换器  
        self.html_text_converter = self.get_html_text_converter()  
          
        # 初始化浏览器环境进程  
        multiprocessing.set_start_method('spawn', force=True)  
        self.browser_side, self.agent_side = multiprocessing.Pipe()  
          
        # 初始化浏览器  
        self.init_browser()  
          
        # 注册程序退出时的清理函数  
        atexit.register(self.close)  
          
    def get_html_text_converter(self) -> html2text.HTML2Text:  
        """初始化HTML到文本的转换器"""  
        html_text_converter = html2text.HTML2Text()  
        # 不忽略链接，但忽略图片  
        html_text_converter.ignore_links = False  
        html_text_converter.ignore_images = True  
        # 使用alt文本替代图片  
        html_text_converter.images_to_alt = True  
        # 禁用自动文本换行  
        html_text_converter.body_width = 0  
        return html_text_converter  
      
    def init_browser(self) -> None:  
        """初始化浏览器进程"""  
        try:  
            self.process = multiprocessing.Process(target=self.browser_process)  
            self.process.start()  
        except Exception as e:  
            print(f'启动浏览器进程失败: {e}')  
            raise  
          
        if not self.check_alive(timeout=200):  
            self.close()  
            raise Exception('启动浏览器环境失败')  
      
    def browser_process(self) -> None:  
        """浏览器进程的主函数"""  
        # 创建事件循环  
        loop = asyncio.new_event_loop()  
        asyncio.set_event_loop(loop)  
          
        # 初始化浏览器配置  
        browser_config = BrowserConfig(  
            headless=True,  
            disable_security=True,  
            deterministic_rendering=True  
        )  
          
        # 初始化浏览器上下文配置  
        context_config = BrowserContextConfig(  
            minimum_wait_page_load_time=0.5,  
            wait_for_network_idle_page_load_time=1.0,  
            maximum_wait_page_load_time=5.0,  
            browser_window_size={  
                "width": 1280,  
                "height": 800  
            },
            highlight_elements=True,
        )  
          
        # 初始化控制器和浏览器  
        browser_instance = None  
        browser_context = None  
          
        try:  
            # 创建浏览器实例和上下文  
            browser_instance = Browser(config=browser_config)  
            browser_context = loop.run_until_complete(browser_instance.new_context(config=context_config))  
              
            # 初始化完成  
            print('浏览器环境已启动')  
              
            # 导航到默认页面  
            loop.run_until_complete(self._navigate_to_url(browser_context, "about:blank"))  
              
            # 主循环：处理来自agent的请求  
            while True:  
                if self.browser_side.poll(timeout=0.01):  
                    unique_request_id, action_data = self.browser_side.recv()  
                      
                    # 处理关闭请求  
                    if unique_request_id == 'SHUTDOWN':  
                        print('关闭浏览器环境...')  
                        loop.run_until_complete(browser_context.close())  
                        loop.run_until_complete(browser_instance.close())  
                        return  
                      
                    # 处理存活检查请求  
                    elif unique_request_id == 'IS_ALIVE':  
                        self.browser_side.send(('ALIVE', None))  
                        continue  
                      
                    # 处理浏览器动作  
                    action = action_data['action']
                    action_execution_error_message = None
                      
                    # 处理不同类型的动作  
                    try:  
                        if action.startswith('goto:'):  
                            url = action[5:]
                            if url.startswith('"') and url.endswith('"'):
                                url = url[1:-1]
                            result = loop.run_until_complete(self._navigate_to_url(browser_context, url))  
                        elif action.startswith('click:'):  
                            element_index = int(action[6:])  
                            result = loop.run_until_complete(self._click_element(browser_context, element_index))
                            if "error" in result:
                                action_execution_error_message = result["error"]
                        elif action.startswith('type:'):  
                            parts = action[5:].split(':', 1)  
                            if len(parts) == 2:  
                                element_index, text = int(parts[0]), parts[1]  
                                result = loop.run_until_complete(self._input_text(browser_context, element_index, text))
                                if "error" in result:
                                    action_execution_error_message = result["error"] 
                            else:  
                                result = {"error": "格式错误，应为 type:索引:文本"}  
                        elif action.startswith('scroll:'):  
                            direction = action[7:]  
                            if direction == 'down':  
                                result = loop.run_until_complete(self._scroll_down(browser_context))  
                            else:  
                                result = {"error": "滚动方向无效"}  
                        else:  
                            result = {"error": f"不支持的动作: {action}"}                                   
                        # 获取页面状态  
                        obs = loop.run_until_complete(self._get_observation(browser_context))  
                        if action_execution_error_message:
                            obs["error_message_for_step"] = action_execution_error_message
      
                        # 发送响应  
                        self.browser_side.send((unique_request_id, obs))  
                          
                    except Exception as e:  
                        error_obs: dict = {
                            "url": "unknown",
                            "title": "unknown",
                            "text_content": f"处理动作 '{action}' 时发生严重错误: {str(e)}",
                            "screenshot": None,
                            "set_of_marks": None,
                            "dom_object": {},
                            "axtree_object": {},
                            "active_page_index": 0,
                            "open_pages_urls": [],
                            "goal_image_urls": [],
                            "focused_element_bid": None,
                            "elapsed_time": 0,
                            "extra_element_properties": {},
                            "error_message_for_step": str(e),
                        }
                        self.browser_side.send((unique_request_id, error_obs))  
                          
        except KeyboardInterrupt:  
            print('浏览器环境进程被用户中断')  
        except Exception as e:  
            print(f'浏览器环境进程出错: {e}')  
        finally:  
            # 清理资源  
            if browser_context:  
                loop.run_until_complete(browser_context.close())  
            if browser_instance:  
                loop.run_until_complete(browser_instance.close())  
            loop.close()  
      
    async def _navigate_to_url(self, browser_context, url):  
        """导航到指定URL"""  
        page = await browser_context.get_current_page()  
        await page.goto(url)  
        await page.wait_for_load_state('load')  
        return {"status": "成功", "url": url}  
      
    async def _click_element(self, browser_context, element_index):  
        """点击元素"""  
        state = await browser_context.get_state(cache_clickable_elements_hashes=True)  
        selector_map = state.selector_map  
          
        if element_index not in selector_map:  
            return {"error": f"元素索引 {element_index} 不存在"}  
              
        element_node = selector_map[element_index]  
        download_path = await browser_context._click_element_node(element_node)  
          
        if download_path:  
            return {"status": "成功", "download_path": download_path}  
        return {"status": "成功", "element_text": element_node.get_all_text_till_next_clickable_element(max_depth=2)}  
      
    async def _input_text(self, browser_context, element_index, text):  
        """在元素中输入文本"""  
        state = await browser_context.get_state(cache_clickable_elements_hashes=True)  
        selector_map = state.selector_map  
          
        if element_index not in selector_map:  
            return {"error": f"元素索引 {element_index} 不存在"}  
              
        element_node = selector_map[element_index]  
        await browser_context._input_text_element_node(element_node, text)  
        return {"status": "成功", "text": text}  
      
    async def _scroll_down(self, browser_context):  
        """向下滚动"""  
        page = await browser_context.get_current_page()  
        await page.evaluate('window.scrollBy(0, window.innerHeight);')  
        return {"status": "成功", "direction": "down"}  
      
    async def _get_observation(self, browser_context):  
        """获取当前浏览器状态的观察结果"""  
        # 获取浏览器状态  
        state = await browser_context.get_state(cache_clickable_elements_hashes=True)  
          
        # 获取当前页面  
        page = await browser_context.get_current_page()  
          
        # 获取DOM结构  
        html_str = await page.content()  
        text_content = self.html_text_converter.handle(html_str)  
          
        # 获取截图  
        screenshot = await page.screenshot()
        screenshot_base64 = self._image_to_base64(screenshot)  

        # 构建观察结果
        current_url = page.url
        obs = {  
            "url": current_url,  
            "title": await page.title(),  
            "text_content": text_content,  
            "screenshot": screenshot_base64,  
            "set_of_marks": screenshot_base64,  
            "dom_object": {},  # 简化处理，实际应用中需要转换DOM结构  
            "axtree_object": {}, # 根据需要填充 AXTree
            "active_page_index": 0, # 当前假设只有一个页面
            "open_pages_urls": [current_url] if current_url else [],
            "goal_image_urls": [], # 根据需要填充
            "focused_element_bid": None, # 根据需要填充
            "elapsed_time": 0, # 简化处理
            "extra_element_properties": {} # 简化处理
        }  
          
        return obs  
      
    def _image_to_base64(self, image_bytes):  
        """将图像转换为base64字符串"""  
        return f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"  
      
    async def step(self, action_str: str) -> dict:  
        """异步执行动作并返回观察结果"""  
        unique_request_id = str(uuid.uuid4())  
        self.agent_side.send((unique_request_id, {'action': action_str}))  
          
        # 使用异步方式等待响应  
        while True:  
            if self.agent_side.poll(timeout=0.01):  
                response_id, obs = self.agent_side.recv()  
                if response_id == unique_request_id:  
                    final_obs = dict(obs) # 创建可变副本

                    # 确保 BrowserOutputObservation 所需的字段存在
                    final_obs.setdefault('url', "")
                    final_obs.setdefault('title', "")
                    final_obs.setdefault('text_content', "")
                    final_obs.setdefault('screenshot', None)
                    final_obs.setdefault('set_of_marks', None)
                    final_obs.setdefault('dom_object', {})
                    final_obs.setdefault('axtree_object', {})
                    final_obs.setdefault('active_page_index', 0)
                    # open_pages_urls 应该基于 obs_from_process 中的 url
                    final_obs.setdefault('open_pages_urls', [final_obs['url']] if final_obs.get('url') else [])
                    final_obs.setdefault('goal_image_urls', [])
                    final_obs.setdefault('focused_element_bid', None)
                    final_obs.setdefault('elapsed_time', 0) # browsergym 会提供这个
                    final_obs.setdefault('extra_element_properties', {})

                    # 处理错误信息和动作相关字段
                    final_obs['last_action'] = action_str # utils.py 会用这个作为 last_browser_action

                    error_message_from_proc = final_obs.pop("error_message_for_step", None)
                    if error_message_from_proc:
                        final_obs['last_action_error'] = error_message_from_proc
                        final_obs['error'] = True
                    else:
                        final_obs['last_action_error'] = ""
                        final_obs['error'] = False
                    return final_obs
            await asyncio.sleep(0.01) # 短暂休眠以避免CPU占用过高  
      
    def check_alive(self, timeout: float = 60) -> bool:  
        """检查浏览器环境是否正常运行"""  
        self.agent_side.send(('IS_ALIVE', None))  
        if self.agent_side.poll(timeout=timeout):  
            response_id, _ = self.agent_side.recv()  
            if response_id == 'ALIVE':  
                return True  
            print(f'浏览器环境未正常运行。响应ID: {response_id}')  
        return False  
      
    def close(self) -> None:  
        """关闭浏览器环境"""  
        if not hasattr(self, 'process') or not self.process.is_alive():  
            return  
              
        try:  
            self.agent_side.send(('SHUTDOWN', None))  
            self.process.join(5)  # 等待进程终止  
              
            if self.process.is_alive():  
                print('浏览器进程未终止，强制终止中...')  
                self.process.terminate()  
                self.process.join(5)  
                  
                if self.process.is_alive():  
                    self.process.kill()  
                    self.process.join(5)  
                      
            self.agent_side.close()  
            self.browser_side.close()  
              
        except Exception as e:  
            print(f'关闭浏览器环境时出错: {e}')  
  
# 使用示例  
async def example_usage():
    browser_env = BrowserUseEnv()
    # 导航到网页 - utils.py 会发送类似 'goto:"https://www.google.com"' 的动作
    observation = await browser_env.step('goto:"https://www.google.com"')
    print(f"当前页面URL: {observation.get('url')}") # 使用 .get 以防字段缺失
    print(f"当前页面标题: {observation.get('title')}")
    print(f"错误信息: {observation.get('last_action_error')}")
    # 尝试一个会产生错误的动作
    observation = await browser_env.step('click:999') # 假设索引999不存在
    print(f"点击不存在元素后的URL: {observation.get('url')}")
    print(f"错误: {observation.get('error')}")
    print(f"错误信息: {observation.get('last_action_error')}")
    print(f"文本内容截断: {observation.get('text_content', '')}")


    browser_env.close()
  
# 运行示例  
if __name__ == "__main__":  
    asyncio.run(example_usage())