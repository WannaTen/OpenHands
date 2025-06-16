from dataclasses import dataclass, field
from typing import Any

from browsergym.utils.obs import flatten_axtree_to_str

from openhands.core.schema import ActionType, ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class BrowserOutputObservation(Observation):
    """This data class represents the output of a browser."""

    url: str
    trigger_by_action: str
    screenshot: str = field(repr=False, default='')  # don't show in repr
    screenshot_path: str | None = field(default=None)  # path to saved screenshot file
    set_of_marks: str = field(default='', repr=False)  # don't show in repr
    error: bool = False
    observation: str = ObservationType.BROWSE
    goal_image_urls: list[str] = field(default_factory=list)
    # do not include in the memory
    open_pages_urls: list[str] = field(default_factory=list)
    active_page_index: int = -1
    dom_object: dict[str, Any] = field(
        default_factory=dict, repr=False
    )  # don't show in repr
    axtree_object: dict[str, Any] = field(
        default_factory=dict, repr=False
    )  # don't show in repr
    extra_element_properties: dict[str, Any] = field(
        default_factory=dict, repr=False
    )  # don't show in repr
    last_browser_action: str = ''
    last_browser_action_error: str = ''
    focused_element_bid: str = ''

    @property
    def message(self) -> str:
        return 'Visited ' + self.url

    def __str__(self) -> str:
        ret = (
            '**BrowserOutputObservation**\n'
            f'URL: {self.url}\n'
            f'Error: {self.error}\n'
            f'Open pages: {self.open_pages_urls}\n'
            f'Active page index: {self.active_page_index}\n'
            f'Last browser action: {self.last_browser_action}\n'
            f'Last browser action error: {self.last_browser_action_error}\n'
            f'Focused element bid: {self.focused_element_bid}\n'
        )
        if self.screenshot_path:
            ret += f'Screenshot saved to: {self.screenshot_path}\n'
        ret += '--- Agent Observation ---\n'
        ret += self.get_agent_obs_text()
        return ret

    def get_agent_obs_text(self) -> str:
        """Get a concise text that will be shown to the agent."""
        if self.trigger_by_action == ActionType.BROWSE_INTERACTIVE:
            text = f'[Current URL: {self.url}]\n'
            text += f'[Focused element bid: {self.focused_element_bid}]\n'

            # Add screenshot path information if available
            if self.screenshot_path:
                text += f'[Screenshot saved to: {self.screenshot_path}]\n'

            text += '\n'

            if self.error:
                text += (
                    '================ BEGIN error message ===============\n'
                    'The following error occurred when executing the last action:\n'
                    f'{self.last_browser_action_error}\n'
                    '================ END error message ===============\n'
                )
            else:
                text += '[Action executed successfully.]\n'

            return text

        elif self.trigger_by_action == ActionType.BROWSE:
            text = f'[Current URL: {self.url}]\n'

            if self.error:
                text += (
                    '================ BEGIN error message ===============\n'
                    'The following error occurred when trying to visit the URL:\n'
                    f'{self.last_browser_action_error}\n'
                    '================ END error message ===============\n'
                )
            text += '============== BEGIN webpage content ==============\n'
            text += self.content
            text += '\n============== END webpage content ==============\n'
            return text
        else:
            raise ValueError(f'Invalid trigger_by_action: {self.trigger_by_action}')
