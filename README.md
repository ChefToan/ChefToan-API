# Progression Chart Image Generator Server (Clash of Clans Legend League)
A simple Flask application that fetches Legend League data from Clash of Clans and ClashPerk APIs, then generates a matplotlib chart showing daily trophy progression.

## Features

- Fetches player data (league, clan, trophies)
- Displays a progression chart for the Legend League season as PNG image format
- Uses a redesigned chart layout (top banner, middle row stats, bottom row chart)

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourname/my_project.git
   cd my_project
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file and add your tokens:
   ```bash
   COC_API_TOKEN="YOUR_COC_API_TOKEN"
   CLASHPERK_API_TOKEN="YOUR_CLASHPERK_API_TOKEN"
   ```

5. Run the Flask app:
   ```bash
   python app.py
   ```

6. Open your browser at `http://127.0.0.1:5000/chart/<player_tag>`.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT