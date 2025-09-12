# AI Prompts Management Guide

This guide explains how to easily refine and manage AI system messages for your Media Monitoring Agent.

## 🎯 Quick Start

### 1. **View Current Prompts**
```bash
python manage_ai_prompts.py
# Select option 1 to view all current prompts
```

### 2. **Edit Prompts**
```bash
python manage_ai_prompts.py
# Select option 2 to edit prompts interactively
```

### 3. **Test Prompts**
```bash
python manage_ai_prompts.py
# Select option 3 to test prompts with sample content
```

## 📁 File Structure

```
├── ai_prompts.py              # Main configuration file
├── manage_ai_prompts.py       # Interactive management tool
├── AI_PROMPTS_GUIDE.md        # This guide
└── services/ai_service.py     # Updated to use configuration
```

## 🔧 How It Works

### Configuration-Based Approach
- **All AI prompts are stored in `ai_prompts.py`**
- **No need to touch core application code**
- **Easy to version control and track changes**
- **Supports different prompts for different use cases**

### Key Components

1. **System Messages**: Define the AI's role and behavior
2. **User Templates**: Define how user content is formatted
3. **Model Configurations**: Control AI model parameters

## 📝 Available Prompt Types

### 1. **Article Summary** (`article_summary`)
- **Purpose**: Summarize news articles for political/policy analysis
- **System Message**: Defines the AI as a media analyst
- **User Template**: Formats article content for analysis

### 2. **Report Synthesis** (`report_synthesis`)
- **Purpose**: Create executive summaries from multiple articles
- **System Message**: Defines the AI as a policy analyst
- **User Template**: Formats multiple summaries into reports

### 3. **Hansard Questions** (`hansard_questions`)
- **Purpose**: Generate parliamentary questions from media coverage
- **System Message**: Defines the AI as a parliamentary affairs specialist
- **User Template**: Formats media content for question generation

## 🛠️ Making Changes

### Method 1: Direct File Editing
1. Open `ai_prompts.py`
2. Modify the desired system message or template
3. Save the file
4. Restart your application

### Method 2: Interactive Tool
1. Run `python manage_ai_prompts.py`
2. Select "Edit prompts interactively"
3. Choose the prompt type to edit
4. Make your changes
5. The tool will show you the updated prompts

### Method 3: Programmatic Updates
```python
from ai_prompts import PROMPT_TEMPLATES

# Update a system message
PROMPT_TEMPLATES["article_summary"]["system"] = "Your new system message here"

# Update a user template
PROMPT_TEMPLATES["article_summary"]["user_template"] = "Your new template here"
```

## 🧪 Testing Your Changes

### Using the Management Tool
1. Run `python manage_ai_prompts.py`
2. Select "Test prompts with sample content"
3. Choose a prompt type
4. Enter sample content or use the default
5. Review the formatted prompt

### Testing in Production
1. Make your changes to `ai_prompts.py`
2. Restart the Docker container: `docker-compose restart media-monitoring-agent`
3. Test the "Process All Manual Articles" functionality
4. Check the generated reports for quality

## 📊 Model Configuration

You can also adjust AI model parameters in `ai_prompts.py`:

```python
MODEL_CONFIGS = {
    "gemini-1.5-flash": {
        "temperature": 0.3,    # Lower = more consistent, Higher = more creative
        "max_tokens": 1000,    # Maximum response length
        "top_p": 0.8          # Controls diversity of responses
    }
}
```

## 🔄 Best Practices

### 1. **Version Control**
- Always commit changes to `ai_prompts.py`
- Use descriptive commit messages
- Consider creating branches for major prompt changes

### 2. **Testing**
- Test changes with sample content before deploying
- Monitor the quality of generated reports
- Keep track of what works and what doesn't

### 3. **Iterative Improvement**
- Start with small changes
- Test each change thoroughly
- Document what works for your specific use case

### 4. **Backup**
- Keep a backup of working prompt configurations
- Consider creating different prompt sets for different scenarios

## 🚨 Troubleshooting

### Common Issues

1. **Import Error**: Make sure `ai_prompts.py` is in the same directory as your application
2. **Template Error**: Check that your templates have the correct placeholders (e.g., `{title}`, `{content}`)
3. **No Changes Applied**: Restart the Docker container after making changes

### Getting Help

1. Check the logs: `docker-compose logs media-monitoring-agent`
2. Test prompts with the management tool
3. Verify your changes are saved correctly

## 📈 Monitoring Success

### Key Metrics to Watch
- **Report Quality**: Are the generated summaries relevant and useful?
- **Consistency**: Are similar articles producing similar quality summaries?
- **Relevance**: Are the summaries focused on political/policy aspects as intended?

### A/B Testing
- Create different prompt versions
- Test with the same content
- Compare results and choose the best performing version

---

**Remember**: The goal is to create AI prompts that produce high-quality, relevant summaries for your specific use case. Don't hesitate to experiment and iterate!
