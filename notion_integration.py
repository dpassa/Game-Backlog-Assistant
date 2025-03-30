from notion_client import Client
import json

class NotionIntegration:
    def __init__(self, auth_token):
        self.client = Client(auth=auth_token)

    def write_text(self, page_id, text, type='paragraph'):
        self.client.blocks.children.append(
            block_id=page_id,
            children=[{
                "object": "block",
                "type": type,
                type: {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }]
        )

    def write_dict_to_file_as_json(self, content, file_name):
        content_as_json_str = json.dumps(content)
        with open(file_name, 'w') as f:
            f.write(content_as_json_str)

    def read_text(self, page_id):
        response = self.client.blocks.children.list(block_id=page_id)
        return response['results']

    def create_simple_blocks_from_content(self, content):
        page_simple_blocks = []
        for block in content:
            block_id = block['id']
            block_type = block['type']
            has_children = block['has_children']
            rich_text = block[block_type].get('rich_text')

            if not rich_text:
                return

            simple_block = {
                'id': block_id,
                'type': block_type,
                'text': rich_text[0]['plain_text']
            }

            if has_children:
                nested_children = self.read_text(block_id)
                simple_block['children'] = self.create_simple_blocks_from_content(nested_children)

            page_simple_blocks.append(simple_block)

        return page_simple_blocks

    def write_row(self, database_id, coverLink, title, consoles, releaseDate, online, genres, length, related_page_id):
        cleaned_genres = [{'name': genre['name'].replace(',', '')} for genre in genres]
        cleaned_consoles = [{'name': console['name'].replace(',', '')} for console in consoles]
        cleaned_online = [{'name': online_option['name'].replace(',', '')} for online_option in online]

        self.client.pages.create(
            **{
                "parent": {
                    "database_id": database_id
                },
                "cover": {
                    "type": "external",
                    "external": {
                        "url": coverLink
                    }
                },
                'properties': {
                    'title': {'title': [{'text': {'content': title}}]},
                    'Status': {'select': {'name': "Backlog"}},
                    'Release Date': {'date': {'start': releaseDate}},
                    'genre': {'multi_select': cleaned_genres},
                    'Console': {'multi_select': cleaned_consoles},
                    'Online': {'multi_select': cleaned_online},
                    'Length': {'number': length},
                    'Store': {'relation': [{'id': related_page_id}]}
                }
            }
        )
