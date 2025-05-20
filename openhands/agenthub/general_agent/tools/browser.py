
from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_BROWSER_DESCRIPTION = """Interact with the browser by providing action strings. Use this tool ONLY when you need to interact with a webpage.
The 'code' parameter should contain a single action string to be executed by the browser.

See the detailed format for action strings in the description of the 'code' parameter.

Multiple actions can be provided at once, one action per line, but will be executed sequentially without any feedback from the page.
More than 2-3 actions usually leads to failure or unexpected behavior. Example:
"goto:https://www.example.com"
"click:12"
"type:23:my search query"
"scroll:down"

the normal multiple actions can be like this(first type and then click):
"type:7:my search query"
"click:8"



You can also use the browser to view local pdf, png, jpg files.
To do this, first obtain the server URL (e.g., from /tmp/oh-server-url). Then, use an action string like:
`goto:http://{server_url}/view?path={absolute_file_path}`
For example: `goto:http://localhost:8000/view?path=/workspace/test_document.pdf`
Note: The file should be downloaded to the local machine first before attempting to view it with the browser.
"""

_BROWSER_TOOL_DESCRIPTION = """
The following 4 actions are available. Actions are specified as strings in the format 'ACTION_NAME:PARAMETERS'.

goto:URL
    Description: Navigate to a URL. The URL can optionally be enclosed in double quotes.
    Examples:
        goto:http://www.example.com
        goto:"https://www.google.com"

click:ELEMENT_INDEX
    Description: Click an element identified by its integer index. Element indices are typically obtained from the browser observation.
    Examples:
        click:12
        click:0

type:ELEMENT_INDEX:TEXT
    Description: Type text into an element (e.g., an input field) identified by its integer index. The text to type follows the second colon.
    Examples:
        type:23:hello world
        type:45:user@example.com

scroll:DIRECTION
    Description: Scroll the page.
    Parameters:
        DIRECTION: The direction to scroll. Currently, only "down" is supported.
    Examples:
        scroll:down
"""

BrowserTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='browser',
        description=_BROWSER_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'code': {
                    'type': 'string',
                    'description': (
                        'The action string that interacts with the browser.\n'
                        + _BROWSER_TOOL_DESCRIPTION
                    ),
                }
            },
            'required': ['code'],
        },
    ),
)
