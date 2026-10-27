# Inventory AI Agent - EECE 430 Assignment 5

## Build and run

Open a terminal in `inventory`:

```powershell
docker build --load -t inventory-agent .
docker run -d --name inventory-agent -p 8000:8000 --env-file .env inventory-agent
```

Open http://localhost:8000. Create a local `.env` file with `GEMINI_API_KEY=your_gemini_api_key` using `.env.example` as a template. The image starts with an empty inventory database. Add items through the agent.

## Run from GitHub

```powershell
git clone https://github.com/theanamansour/eece430-assignment5-inventory-agent.git
cd eece430-assignment5-inventory-agent/inventory
```

Create `.env` with your Gemini API key, then run the build and run commands above.
