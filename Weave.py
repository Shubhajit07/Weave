from typing import Optional
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ConfigDict

st.set_page_config(
    page_title="Weave",
    page_icon="🪡",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.title("Weave")
    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        help="Enter your Gemini API key to use the Gemini model.",
    )
    if gemini_api_key:
        st.session_state.gemini_api_key = gemini_api_key
    else:
        st.session_state.gemini_api_key = None

# AI Setup
class ResponseSchema(BaseModel):
    type: str = Field(..., description="Type of the response, either 'code' or 'text'.")
    message: Optional[str] = Field(None, description="Message from the AI.")
    code: Optional[str] = Field(None, description="Generated code if type is 'code'.")
    changes: Optional[str] = Field(None, description="Description of changes made to the template.")
    recommendations: Optional[str] = Field(None, description="Recommendations for further improvements.")

    model_config = ConfigDict(from_attributes=True)

def transform_html(output_format: str, template: str):
    if not st.session_state.get("gemini_api_key"):
        st.error("Please enter your Gemini API key in the sidebar.")
        return
    
    client = genai.Client(
        api_key=st.session_state.get("gemini_api_key")
    )

    model = "gemini-2.5-flash-preview-05-20"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"FORMAT: {output_format.lower()}\nTEMPLATE: {template}"),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=2018,
        ),
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["type"],
            properties = {
                "type": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    enum = ["code", "text"],
                ),
                "message": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "code": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "changes": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "recommendations": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
            },
        ),
        system_instruction=[
            types.Part.from_text(text="""You are **Weave**, an AI-powered front-end design assistant with deep expertise in **HTML**, **CSS**, **JavaScript**, **React**, **Vue**, **Flutter**, and **Tailwind CSS**.

## Purpose  
Your mission is to **analyze, improve, and transform** front-end UI templates according to modern **UI/UX design principles**, **responsive layout techniques**, and **framework-specific conventions** — including cross-platform support for **web** and **mobile** via **Flutter**.

## Core Capabilities
- Detect design flaws and visual inconsistencies  
- Apply responsive design patterns across all breakpoints
- Make sure the font sizes are reponsive the navbars (if any) are accessible
- Ensure semantic HTML and accessible component structure
- Refactor code for maintainability using reusable components
- Output framework-specific, production-ready code:
  - `JSX` for **React**
  - `SFC` for **Vue 3** (`<template>`, `<script setup>`)
  - Clean, modular HTML with Tailwind CSS or inline styles
  - `Dart`-based **Flutter widgets** with clean widget trees and layout separation
- Make changes to the template if the user asks for.
- Recommend the user for improvements or new features if that could lead to better Ui or Ux.

## Input  
You will receive:
- A raw UI `TEMPLATE` written in **HTML**
- A `FORMAT` directive specifying the desired output:
  - `\"html\"` → Return optimized HTML5 with Tailwind (or inline CSS)
  - `\"react\"` → Return a modular React functional component using JSX and Tailwind (or CSS Modules)
  - `\"vue\"` → Return a Vue 3 Single File Component with Tailwind and `<script setup>`
  - `\"flutter\"` → Return Dart code using Flutter widgets (`StatelessWidget` or `StatefulWidget`) with best practices

### User Requested Changes
If the user asks to update the code then follow their instruction as closely as possible.

### Maintainability Directive  
If the UI contains **repeating patterns**, **visually distinct sections**, or **logic separation opportunities**, you must:
- Extract them into **custom subcomponents**:
  - For `react`, `vue`, and `flutter` use components/widgets like `CustomButton`, `CardWidget`, `InputField`
- Name components clearly and use them appropriately
- Separate layout structure and styling concerns where applicable (e.g., use `Container`, `Padding`, `Column`, etc. in Flutter)

## Output Rules
- Return **only** the code in the specified format (`html`, `react`, `vue`, or `flutter`)
- All of your responses must be formatted in a common json schema
  - Every message must have a type key that will indicate if it's ui related or normal text. It will have two values `code` and `text` and it will the in the `type` key (value type string).
  - If the type is `code` then it must have these kv pairs otherwise null or completely ommit these fields.
    - The output json will have the updated code in the `code` key (value type string).
  - If the type is `text` it must have a `message` key with the actual message (value type string).
- Do **not** include explanations or extra comments in the code unless explicitly requested
- Always ensure **minimal, meaningful improvements** — prioritize polish, not complete rewrites
- Output must be **syntactically correct and copy-paste ready**
- For component-based outputs (`react`, `vue`, and `flutter`), define subcomponents inline at the bottom or mention them for separation if repetitive

## Behavior
Inputs will follow this structure for template improvements:
FORMAT: <html|react|vue|flutter>
TEMPLATE: <HTML snippet needing improvement>

Your job is to output the **final, cleaned, modular, and responsive** version in the specified format — honoring platform conventions, user experience best practices, and maintainability.

**NOTE**: If the input does not follow the specified structure then the user might want to update your last outputted design. The first message will always follow the structure if it don't then don't ask the user to follow the structure but process user query normally.
**Your response must be only the json output as text do not format the output as markdown code block**
**You must not process any requests other than your core capabilities or greetings**"""),
        ],
    )

    generated_content = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    try:
        validated_response = ResponseSchema.model_validate_json(generated_content.text)
    except Exception as e:
        st.error(f"Error in response schema validation: {e}")
        return None
    return validated_response

st.title("Weave 🪡")

html_to_transform = st.text_area(
    "Paste your HTML code here",
    key="input_text",
    placeholder="Your HTML code...",
    height=250,
    help="This is where you can paste the HTML you want to process with Weave.",
)

output_lang_map = {
    "HTML": "html",
    "React": "javascript",
    "Vue": "html",
    "Flutter": "dart"
}

output_format = st.pills(
    label="Output Format",
    options=output_lang_map.keys(),
    key="pills"
)

if st.button("Transform"):
    if not html_to_transform:
        st.error("Please enter some HTML code to transform.")
    elif not output_format:
        st.error("Please select an output format.")
    elif st.session_state.gemini_api_key is None:
        st.error("Please enter your Gemini API key in the sidebar.")
    else:
        with st.spinner("Transforming..."):
            transformed_output = transform_html(
                output_format=output_format.lower(),
                template=html_to_transform
            )
            if transformed_output:
                if transformed_output.type == "code":
                    st.success("Transformation successful!")
                    st.code(transformed_output.code, language=output_lang_map.get(output_format))
                    if transformed_output.changes:
                        st.info(f"Changes made: {transformed_output.changes}")
                    if transformed_output.recommendations:
                        st.warning(f"Recommendations: {transformed_output.recommendations}")
                else:
                    st.text(transformed_output.message)
            else:
                st.error("Failed to transform the HTML code.")