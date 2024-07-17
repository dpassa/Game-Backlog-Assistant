
# Game Backlog Assistant

This project will help easily add to your game backlog

# README IS A WORK IN PROGRESS

## Notion Setup

1. Create a notion account at https://www.notion.so/signup

2. Create a copy of the Video Game Backlog Tracker at https://www.notion.so/templates/video-game-tracker

3. Create a new integration at https://www.notion.so/profile/integrations

4. Allow the integration to Read, Update, and Insert Content

5. Take note of the Internal Integration Secret Key for later

6. Go back to your copy of the Video Game Backlog Tracker and Add a new Connection to your previously created integration

- ![Alt text](/images/Connection1.png)
- ![Alt text](/images/Connection2.png)



```py
    
```
</details>

## Installation
1. Clone this repository:

```
git clone https://github.com/Rumpkin/Game-Backlog-Assistant.git
cd Game-Backlog-Assistant
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```
3. Set up your environment variables:

- Open the secrets.json file in the project root directory
- Add the following environment variables as requested
- Example:
```
{
    "notion_token" : "YourNotionToken",
    "notion_page_id" : "Notion_Page_ID",
    "notion_database_id" : "Notion_Database_ID",
    "IGDB_clientID" : "IGDB_ClientID",
    "IGDB_secret" : "IGDB_Secret"
}
```

### Not sure how to find an environment variable look below 

<details>
<summary>Finding Your Notion Client ID</summary>

You can find your Client ID under the settings for the integretion you created while setting up notion

> Integration link: https://www.notion.so/profile/integrations

![Alt text](/images/Integration_Secret_Key_Referenece1.png)

```py
    
```
</details>

<details>
<summary>Finding Your Notion Page ID</summary>

### Ur Cooked Mate

```py
    
```
</details>

<details>
<summary>Finding Your Notion Database ID</summary>


```

```
</details>

<details>
<summary>Finding Your IGDB Client ID</summary>

```
a
```
</details>

<details>
<summary>Finding Your IGDB Secret Token</summary>


```
a
```
</details>

## Usage

Run the main script to start the program:

```
python main.py
```

Once started, the program will prompt you with whether you want to add a single game or a list of games:

```
Single Game? y/n 
```

If you type yes it will prompt you for the game's title 

```
Single Game? y/n y
Game title: 
```

And then add it to the notion database

```
Single Game? y/n y
Game title: Spiritfarer
--- Adding Spiritfarer ---
Game Platforms: PC (Microsoft Windows), Google Stadia, PlayStation 4, Xbox One, Linux, Mac, Nintendo Switch
Game Release Date: 2020-08-17
Game Genres: Platform, Action, Fantasy
Game Added to Database
```

If you type no it will try to locate a file name "games.txt" and will add all the games located in the file

```
Single Game? y/n n
--- Adding Tunic ---
Game Added to Database
--- Adding Celeste ---
Game Added to Database
--- Adding Katana Zero ---
Game Added to Database
--- Adding Ghost of Tsushima ---
Game Added to Database
```

After adding a game to the database the program will delete the title from the games.txt file