# Venice.ai Setup Guide

## Quick Setup Steps

### 1. Get your Venice.ai API Key
1. Go to [Venice.ai](https://venice.ai)
2. Sign up or log in to your account
3. Navigate to your API settings
4. Copy your API key (it should start with `vn_`)

### 2. Configure the API Key
Edit the file `backend/.env` and replace:
```
VENICE_API_KEY=your_venice_api_key_here
```

With your actual API key:
```
VENICE_API_KEY=vn_your_actual_api_key_here
```

### 3. Test the Connection
Run the test script to verify your API key works:
```bash
cd backend
python test_venice_connection.py
```

You should see:
```
✅ SUCCESS: Connected to Venice.ai!
📝 Response: {"message": "Hello, Venice.ai!"}
```

### 4. Start the Application
Once the test passes, start the full application:
```bash
make start
```

## What Changed

- **No more mock responses**: The system now connects directly to Venice.ai
- **Real AI analysis**: All pose context analysis, character processing, and pose enhancement now use actual AI
- **Better responses**: The AI will provide contextually appropriate responses based on your actual pose text

## Troubleshooting

### "API key is required" error
- Make sure you've set `VENICE_API_KEY` in `backend/.env`
- Check that there are no extra spaces or quotes around the key

### "Please set your actual Venice.ai API key" error
- You need to replace `your_venice_api_key_here` with your real API key
- Make sure the key starts with `vn_`

### Connection timeout or network errors
- Check your internet connection
- Verify your API key is valid and not expired
- Try the test script again

## Using the Application

Once connected to Venice.ai, all features will work with real AI:

1. **Pose Context Analysis**: Analyzes real poses and extracts meaningful context
2. **Character Brain Dump**: Processes character descriptions into structured profiles  
3. **Pose Enhancement**: Improves poses with AI-generated narrative details

The responses will be much more intelligent and contextually appropriate than the previous mock responses! 