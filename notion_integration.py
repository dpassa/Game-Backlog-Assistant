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

    def check_game_exists(self, database_id, title):
        """
        Check if a game with the given title already exists in the database.

        Args:
            database_id: Notion database ID
            title: Game title to search for

        Returns:
            Tuple of (exists: bool, page_id: str or None)
        """
        try:
            response = self.client.databases.query(
                database_id=database_id,
                filter={
                    "property": "title",
                    "title": {
                        "equals": title
                    }
                }
            )

            results = response.get('results', [])
            if results:
                # Game exists, return the page ID
                return True, results[0]['id']

            return False, None

        except Exception as e:
            print(f"Warning: Error checking for duplicate '{title}': {e}")
            # If check fails, assume it doesn't exist to avoid blocking
            return False, None

    def write_row(self, database_id, cover_link, title, consoles, release_date, online, genres, length, related_page_id, skip_duplicates=True):
        """
        Create a new game entry in Notion database.

        Args:
            database_id: Notion database ID
            cover_link: URL to cover image
            title: Game title
            consoles: List of platforms
            release_date: Release date tuple (date_string, failed_flag) or just date_string
            online: List of game modes
            genres: List of genres
            length: Hours to complete
            related_page_id: Store relation page ID
            skip_duplicates: If True, skip if game already exists (default: True)

        Returns:
            Tuple of (created: bool, message: str)
        """
        # Check for duplicates if enabled
        if skip_duplicates:
            exists, _ = self.check_game_exists(database_id, title)
            if exists:
                return False, f"Game '{title}' already exists in database (skipped)"

        # Handle release_date - extract string from tuple if needed
        if isinstance(release_date, tuple):
            date_string = release_date[0]  # Extract date string from tuple
        else:
            date_string = release_date  # Already a string

        cleaned_genres = [{'name': genre['name'].replace(',', '')} for genre in genres]
        cleaned_consoles = [{'name': console['name'].replace(',', '')} for console in consoles]
        cleaned_online = [{'name': online_option['name'].replace(',', '')} for online_option in online]

        try:
            self.client.pages.create(
                **{
                    "parent": {
                        "database_id": database_id
                    },
                    "cover": {
                        "type": "external",
                        "external": {
                            "url": cover_link
                        }
                    },
                    'properties': {
                        'title': {'title': [{'text': {'content': title}}]},
                        'Status': {'select': {'name': "Backlog"}},
                        'Release Date': {'date': {'start': date_string}},
                        'genre': {'multi_select': cleaned_genres},
                        'Console': {'multi_select': cleaned_consoles},
                        'Online': {'multi_select': cleaned_online},
                        'Length': {'number': length},
                        'Store': {'relation': [{'id': related_page_id}]}
                    }
                }
            )
            return True, f"Game '{title}' added successfully"

        except Exception as e:
            return False, f"Error adding game '{title}': {e}"
