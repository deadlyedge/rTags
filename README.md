# rTags: Tag Extractor API

rTags is a REST API built with FastAPI that extracts relevant tags from a given text and a list of reference websites. It leverages the Perplexity API to analyze the input and generate insightful tags.

## Features

*   **Tag Extraction:** Extracts up to 5 relevant tags from provided text and reference websites.
*   **Perplexity API Integration:** Utilizes the Perplexity API for intelligent tag generation.
*   **FastAPI Framework:** Built with FastAPI for high performance, automatic API documentation, and ease of use.
*   **Input Validation:** Validates input data (text and reference websites) to ensure proper API operation.
* **Error Handling:** Includes error handling for network issues, API errors, and invalid input.
* **Configurable Model:** Easy to change the perplexity model.

## Getting Started

### Prerequisites

*   **Python 3.8+**
*   **Perplexity API Key:** You will need a Perplexity API key to use this application. You can obtain one by signing up on the Perplexity website.

### Installation

1.  **Clone the repository (if applicable):**
    ```bash
    git clone [your_repository_url] # if you have one
    cd rTags
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt # if you have a requirements.txt file.
    # or
    pip install fastapi uvicorn openai pydantic python-dotenv
    ```

4. **Create a `.env` file:**
   In the root directory of the project, create a file named `.env`. Add the following line to the `.env` file, replacing `your_perplexity_api_key` with your actual Perplexity API key:
