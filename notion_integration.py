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

    def check_game_exists_by_external_id(self, database_id, external_id, store_relation_id):
        """
        Check if a game with the given external ID and store already exists in the database.
        This is a more robust duplicate check than title-based matching.

        Args:
            database_id: Notion database ID
            external_id: External store ID (e.g., Steam App ID)
            store_relation_id: Store relation ID (Notion page ID of the store)

        Returns:
            Tuple of (exists: bool, page_id: str or None)
        """
        try:
            # Query using compound filter: External ID AND Store relation
            response = self.client.databases.query(
                database_id=database_id,
                filter={
                    "and": [
                        {
                            "property": "External ID",
                            "rich_text": {
                                "equals": str(external_id)
                            }
                        },
                        {
                            "property": "Store",
                            "relation": {
                                "contains": store_relation_id
                            }
                        }
                    ]
                }
            )

            results = response.get('results', [])
            if results:
                # Game exists, return the page ID
                return True, results[0]['id']

            return False, None

        except Exception as e:
            print(f"Warning: Error checking for duplicate (external_id={external_id}, store={store_relation_id}): {e}")
            # If check fails, fall back to title-based check to avoid blocking
            return False, None

    def get_all_games(self, database_id):
        """
        Retrieve all games from Notion database with title, external_id, Store relation, and Status.

        Args:
            database_id: Notion database ID

        Returns:
            List of dictionaries containing game data
        """
        try:
            all_games = []
            has_more = True
            start_cursor = None

            while has_more:
                query_params = {"database_id": database_id}
                if start_cursor:
                    query_params["start_cursor"] = start_cursor

                response = self.client.databases.query(**query_params)

                for page in response.get('results', []):
                    properties = page.get('properties', {})

                    # Extract title
                    title_prop = properties.get('title', {}).get('title', [])
                    title = title_prop[0].get('text', {}).get('content', '') if title_prop else ''

                    # Extract external ID
                    external_id_prop = properties.get('External ID', {}).get('rich_text', [])
                    external_id = external_id_prop[0].get('text', {}).get('content', '') if external_id_prop else ''

                    # Extract Store relation
                    store_relation = properties.get('Store', {}).get('relation', [])
                    store_id = store_relation[0].get('id', '') if store_relation else ''

                    # Extract Status
                    status_prop = properties.get('Status', {}).get('select', {})
                    status = status_prop.get('name', '') if status_prop else ''

                    all_games.append({
                        'page_id': page['id'],
                        'title': title,
                        'external_id': external_id,
                        'store_id': store_id,
                        'status': status
                    })

                has_more = response.get('has_more', False)
                start_cursor = response.get('next_cursor')

            return all_games

        except Exception as e:
            print(f"Error retrieving games from Notion: {e}")
            return []

    def update_game_status_and_achievements(self, page_id, status=None, achievement_percentage=None):
        """
        Update game status and achievement percentage in Notion.

        Args:
            page_id: Notion page ID
            status: Game status (Currently Playing, Backlog, Complete, On Hold, Abandoned)
            achievement_percentage: Achievement completion percentage (0-100)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            properties = {}

            if status:
                properties['Status'] = {'select': {'name': status}}

            if achievement_percentage is not None:
                properties['Achievements'] = {'number': achievement_percentage}

            if properties:
                self.client.pages.update(page_id=page_id, properties=properties)
                return True, f"Updated game with status: {status}, achievements: {achievement_percentage}%"

            return False, "No updates to apply"

        except Exception as e:
            return False, f"Error updating game: {e}"

    def write_row(self, database_id, cover_link, title, consoles, release_date, online, genres, length, related_page_id, external_id=None, initial_status='Backlog', achievement_percentage=0):
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
            external_id: External store ID (e.g., Steam App ID, GOG product ID)
            initial_status: Initial game status (default: 'Backlog')
            achievement_percentage: Initial achievement percentage (default: 0)

        Returns:
            Tuple of (created: bool, message: str)
        """
        # Ensure title is a proper string (no need to encode/decode)
        title = str(title)



        # Handle release_date - extract string from tuple if needed
        if isinstance(release_date, tuple):
            date_string = release_date[0]  # Extract date string from tuple
        else:
            date_string = release_date  # Already a string

        # Ensure all text fields are proper strings
        def ensure_utf8(text):
            """Ensure text is a proper string"""
            if isinstance(text, str):
                return str(text)
            return text

        cleaned_genres = [{'name': ensure_utf8(genre['name'].replace(',', ''))} for genre in genres]
        cleaned_consoles = [{'name': ensure_utf8(console['name'].replace(',', ''))} for console in consoles]
        cleaned_online = [{'name': ensure_utf8(online_option['name'].replace(',', ''))} for online_option in online]

        try:
            properties = {
                'title': {'title': [{'text': {'content': title}}]},
                'Status': {'select': {'name': initial_status}},
                'Release Date': {'date': {'start': date_string}},
                'genre': {'multi_select': cleaned_genres},
                'Console': {'multi_select': cleaned_consoles},
                'Online': {'multi_select': cleaned_online},
                'Length': {'number': length},
                'Store': {'relation': [{'id': related_page_id}]},
                'External ID': {'rich_text': [{'text': {'content': ensure_utf8(str(external_id))}}]}
            }

            # Add achievements if provided
            if achievement_percentage > 0:
                properties['Achievements'] = {'number': achievement_percentage}

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
                    'properties': properties
                }
            )
            return True, f"Game '{title}' added successfully"

        except Exception as e:
            return False, f"Error adding game '{title}': {e}"
