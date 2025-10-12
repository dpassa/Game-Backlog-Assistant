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

    def check_game_exists_by_external_id(self, database_id, external_id, store_name):
        """
        Check if a game with the given external ID and store already exists in the database.
        This is a more robust duplicate check than title-based matching.

        Args:
            database_id: Notion database ID
            external_id: External store ID (e.g., Steam App ID)
            store_name: Store name (e.g., "Steam", "GOG")

        Returns:
            Tuple of (exists: bool, page_id: str or None)
        """
        try:
            # Query using compound filter: External ID AND Store Name
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
                            "property": "Store Name",
                            "rich_text": {
                                "equals": store_name
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
            print(f"Warning: Error checking for duplicate (external_id={external_id}, store={store_name}): {e}")
            # If check fails, fall back to title-based check to avoid blocking
            return False, None

    def _update_external_id(self, page_id, external_id, store_name):
        """
        Update an existing Notion page with external_id and store_name.
        This is used for transitional migration of legacy entries.

        Args:
            page_id: Notion page ID to update
            external_id: External store ID to add
            store_name: Store name to add

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Ensure UTF-8 encoding
            def ensure_utf8(text):
                if isinstance(text, str):
                    return text.encode('utf-8', errors='replace').decode('utf-8')
                return text

            # Update the page properties
            self.client.pages.update(
                page_id=page_id,
                properties={
                    'External ID': {'rich_text': [{'text': {'content': ensure_utf8(str(external_id))}}]},
                    'Store Name': {'rich_text': [{'text': {'content': ensure_utf8(store_name)}}]}
                }
            )
            print(f"✓ Updated existing entry with external_id={external_id}, store={store_name}")
            return True

        except Exception as e:
            print(f"Warning: Could not update page {page_id} with external_id: {e}")
            # Check if error is due to missing properties
            if "External ID" in str(e) or "Store Name" in str(e):
                print("⚠️  IMPORTANT: Please add 'External ID' and 'Store Name' properties to your Notion database!")
                print("   See MIGRATION_GUIDE.md for instructions")
            return False

    def write_row(self, database_id, cover_link, title, consoles, release_date, online, genres, length, related_page_id, external_id=None, store_name=None, skip_duplicates=True):
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
            store_name: Store name (e.g., "Steam", "GOG")
            skip_duplicates: If True, skip if game already exists (default: True)

        Returns:
            Tuple of (created: bool, message: str)
        """
        # Ensure title is properly encoded as UTF-8 string
        title = str(title).encode('utf-8', errors='replace').decode('utf-8')

        # Check for duplicates if enabled
        if skip_duplicates:
            existing_page_id = None

            # First: Try robust check with external_id + store (for new entries)
            if external_id and store_name:
                exists, existing_page_id = self.check_game_exists_by_external_id(database_id, external_id, store_name)
                if exists:
                    return False, f"Game '{title}' already exists in database (skipped)"

            # Second: Fallback to title-based check (for legacy entries without external_id)
            exists_by_title, existing_page_id = self.check_game_exists(database_id, title)
            if exists_by_title:
                # TRANSITIONAL LOGIC: Update existing entry with external_id if provided
                if external_id and store_name and existing_page_id:
                    update_success = self._update_external_id(existing_page_id, external_id, store_name)
                    if update_success:
                        return False, f"Game '{title}' already exists, updated with external_id (skipped)"
                    else:
                        return False, f"Game '{title}' already exists (skipped, update failed)"

                return False, f"Game '{title}' already exists in database (skipped)"

        # Handle release_date - extract string from tuple if needed
        if isinstance(release_date, tuple):
            date_string = release_date[0]  # Extract date string from tuple
        else:
            date_string = release_date  # Already a string

        # Ensure all text fields are UTF-8 encoded
        def ensure_utf8(text):
            """Ensure text is properly UTF-8 encoded"""
            if isinstance(text, str):
                return text.encode('utf-8', errors='replace').decode('utf-8')
            return text

        cleaned_genres = [{'name': ensure_utf8(genre['name'].replace(',', ''))} for genre in genres]
        cleaned_consoles = [{'name': ensure_utf8(console['name'].replace(',', ''))} for console in consoles]
        cleaned_online = [{'name': ensure_utf8(online_option['name'].replace(',', ''))} for online_option in online]

        try:
            properties = {
                'title': {'title': [{'text': {'content': title}}]},
                'Status': {'select': {'name': "Backlog"}},
                'Release Date': {'date': {'start': date_string}},
                'genre': {'multi_select': cleaned_genres},
                'Console': {'multi_select': cleaned_consoles},
                'Online': {'multi_select': cleaned_online},
                'Length': {'number': length},
                'Store': {'relation': [{'id': related_page_id}]}
            }

            # Add external_id and store_name as rich_text properties if provided
            if external_id:
                properties['External ID'] = {'rich_text': [{'text': {'content': ensure_utf8(str(external_id))}}]}

            if store_name:
                properties['Store Name'] = {'rich_text': [{'text': {'content': ensure_utf8(store_name)}}]}

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
