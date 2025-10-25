"""
Game Status Sync Module

This module syncs game status and achievement data from stores (Steam, GOG) to Notion.
It retrieves games from Notion, fetches their current status and achievements from the store,
and updates Notion accordingly.
"""

from notion_integration import NotionIntegration
from steam_integration import SteamIntegration
from gog_integration import GogIntegration
from consts import (
    NOTION_DATABASE_ID, STEAM_API_KEY, STEAM_USERID_64,
    GOG_PUBLIC_USERNAME, NOTION_TOKEN, NOTION_STORE_STEAM_ID, NOTION_STORE_GOG_ID
)


def sync_game_status(debug=False):
    """
    Main function to sync game status and achievements from stores to Notion.

    Process:
    1. Retrieve all games from Notion database
    2. For each game that's not already 'Complete':
       - Fetch achievement data from the store
       - Calculate status based on last played and achievements
       - Update Notion if status or achievements changed

    Args:
        debug: Enable debug output (default: False)
    """
    print("🔄 Starting Game Status Sync")
    print("=" * 60)

    # Initialize Notion integration
    notion = NotionIntegration(NOTION_TOKEN)

    # Retrieve all games from Notion
    print("📥 Retrieving games from Notion database...")
    notion_games = notion.get_all_games(NOTION_DATABASE_ID)
    print(f"✅ Retrieved {len(notion_games)} games from Notion")

    if not notion_games:
        print("⚠️ No games found in Notion database")
        return

    # Initialize store integrations mapped by store relation ID
    integrations = {}
    store_names = {}  # Map store_id to friendly name for display

    if STEAM_API_KEY and STEAM_USERID_64 and NOTION_STORE_STEAM_ID:
        integrations[NOTION_STORE_STEAM_ID] = SteamIntegration(api_key=STEAM_API_KEY, steamid=STEAM_USERID_64)
        store_names[NOTION_STORE_STEAM_ID] = 'Steam'
        print("✅ Initialized Steam integration")

    if GOG_PUBLIC_USERNAME and NOTION_STORE_GOG_ID:
        integrations[NOTION_STORE_GOG_ID] = GogIntegration(username=GOG_PUBLIC_USERNAME)
        store_names[NOTION_STORE_GOG_ID] = 'GOG'
        print("✅ Initialized GOG integration")

    if not integrations:
        print("❌ No store integrations configured")
        return

    # Track statistics
    stats = {
        'total': 0,
        'updated': 0,
        'skipped_complete': 0,
        'skipped_no_store': 0,
        'errors': 0
    }

    print("\n🔍 Processing games...")
    print("=" * 60)

    # Process each game from Notion
    for i, game in enumerate(notion_games, 1):
        stats['total'] += 1
        title = game.get('title', 'Unknown')
        external_id = game.get('external_id', '')
        store_id = game.get('store_id', '')
        current_status = game.get('status', '')
        page_id = game.get('page_id', '')

        # Get friendly store name for display
        store_display_name = store_names.get(store_id, 'Unknown')

        print(f"\n[{i}/{len(notion_games)}] {title}")
        print(f"  Store: {store_display_name} | External ID: {external_id} | Current Status: {current_status}")

        # Skip if already complete
        if current_status == 'Complete':
            print("  ⊘ Already Complete - skipping")
            stats['skipped_complete'] += 1
            continue

        # Skip if no external ID or store integration not available
        if not external_id or store_id not in integrations:
            print(f"  ⊘ No external ID or store integration not available")
            stats['skipped_no_store'] += 1
            continue

        try:
            integration = integrations[store_id]

            # For Steam, get enriched data with achievements and status
            if store_id == NOTION_STORE_STEAM_ID:
                enriched_data = integration.get_enriched_game_data(external_id)

                if enriched_data:
                    achievement_pct = enriched_data.get('achievement_percentage', 0)
                    new_status = enriched_data.get('status', current_status)

                    print(f"  📊 Achievements: {achievement_pct}%")
                    print(f"  🎯 New Status: {new_status}")

                    # Update Notion if there's new data
                    if new_status != current_status or achievement_pct > 0:
                        success, message = notion.update_game_status_and_achievements(
                            page_id,
                            status=new_status,
                            achievement_percentage=achievement_pct
                        )

                        if success:
                            print(f"  ✅ Updated: {message}")
                            stats['updated'] += 1
                        else:
                            print(f"  ❌ Update failed: {message}")
                            stats['errors'] += 1
                    else:
                        print("  ⊘ No changes needed")
                        stats['skipped_no_store'] += 1
                else:
                    print("  ⚠️ Could not fetch enriched data")
                    stats['errors'] += 1

            # For GOG, we don't have achievement tracking yet
            elif store_id == NOTION_STORE_GOG_ID:
                print("  ⊘ GOG achievement tracking not yet implemented")
                stats['skipped_no_store'] += 1

        except Exception as e:
            print(f"  ❌ Error processing game: {e}")
            stats['errors'] += 1
            if debug:
                import traceback
                traceback.print_exc()

    # Print final statistics
    print("\n" + "=" * 60)
    print("✓ Game Status Sync Completed!")
    print("=" * 60)
    print(f"Total Games Processed: {stats['total']}")
    print(f"Updated: {stats['updated']}")
    print(f"Skipped (Already Complete): {stats['skipped_complete']}")
    print(f"Skipped (No Store/External ID): {stats['skipped_no_store']}")
    print(f"Errors: {stats['errors']}")
    print("=" * 60)


if __name__ == '__main__':
    import sys

    # Parse command line arguments
    debug = '--debug' in sys.argv

    sync_game_status(debug=debug)
