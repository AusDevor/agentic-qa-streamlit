from docling.datamodel.base_models import InputFormat
from docling.document_converter import *
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling_core.types.doc.document import DoclingDocument
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
    TableFormerMode,
)
from docling.datamodel.settings import settings
from docling.backend.msword_backend import MsWordDocumentBackend
from docling.chunking import HybridChunker
import re
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Accelerator and pipeline options
accelerator_options = AcceleratorOptions(
    num_threads=8, device=AcceleratorDevice.CUDA
)
pipeline_options = PdfPipelineOptions(do_table_structure=True, do_ocr=True)
pipeline_options.table_structure_options.do_cell_matching = False
pipeline_options.table_structure_options.mode = TableFormerMode.FAST
pipeline_options.accelerator_options = accelerator_options

# Document converter initialization
doc_converter = (
    DocumentConverter(  # all of the below is optional, has internal defaults.
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.DOCX,
            InputFormat.HTML,
            InputFormat.MD,
        ],  # whitelist formats, non-matching files are ignored.
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=StandardPdfPipeline, backend=PyPdfiumDocumentBackend, pipeline_options=pipeline_options
            ),
            InputFormat.DOCX: WordFormatOption(
                pipeline_cls=SimplePipeline,  backend=MsWordDocumentBackend
            ),
        },
    )
)


class SectionExtractor:
    
    def __init__(self, file_path):
        self.input_path = file_path
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_summary(self, section_content: str) -> dict:
        prompt = f"Summarize the following text and extract keywords:\n\n{section_content}"

        completion = await self.client.chat.completions.create(
        model="o3-mini",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        )

        summary = completion.choices[0].message.content.strip()

        return summary
    
    async def extract_sections_from_txt_async(self, text):
        sections = []
        lines = text.split("\n")

        current_title = None
        current_content = []
        current_start_index = 0
        tasks = []

        for i, line in enumerate(lines):
            if len(line.strip()) < 30 and line.strip():  # Section title condition
                if current_title:  # Save the previous section
                    last_start_index = sections[len(sections)-1]['start_index'] if len(sections) > 0 else 0
                    sections.append({
                        "title": current_title,
                        "start_index": current_start_index,
                        "length": current_start_index - last_start_index,  # Calculate length
                        "text": "\n".join(current_content).strip(),
                        "summary": None
                    })
                    tasks.append(self.generate_summary("\n".join(current_content).strip()))
                current_title = line.strip()
                current_content = []
                current_start_index += len(line)
            else:
                current_content.append(line)
                current_start_index += len(line)

        if current_title:
            last_start_index = sections[len(sections)-1]['start_index'] if len(sections) > 0 else 0
            tasks.append(self.generate_summary("\n".join(current_content).strip()))
            sections.append({
                "title": current_title,
                "start_index": current_start_index,
                "length": current_start_index - last_start_index, 
                "text": "\n".join(current_content).strip(),
                "summary": None
            })

        summaries = await asyncio.gather (* tasks)
        for section, summary in zip (sections, summaries):
            section ['summary'] = summary
            
        return sections

    async def extract_sections_async(self, markdown_text):

        heading_pattern = re.compile(r'^(#{1,6})\s(.+)', re.MULTILINE)

        sections = []
        current_section = None
        tasks = []
        current_index = 0
        current_title = ''

        for match in heading_pattern.finditer(markdown_text):
            heading_text = match.group(2)
            heading_start = match.start()
            heading_end = match.end()

            text = markdown_text[current_index:heading_start].strip()
            if text or current_title:
                sections.append({
                    'title': current_title,
                    'start_index': current_index,
                    'length': heading_start - current_index,
                    'text': text,
                    'summary': None
                })
                tasks.append(self.generate_summary(text))
            
            current_index = heading_end
            current_title = heading_text
        # Add the last section
        text = markdown_text[current_index:].strip()
        if text or current_title:
            sections.append({
                'title': current_title,
                'start_index': current_index,
                'length': len(markdown_text) - current_index,
                'text': text,
                'summary': None
            })
            tasks.append(self.generate_summary(text))

        summaries = await asyncio.gather (* tasks)
        for section, summary in zip (sections, summaries):
            section ['summary'] = summary

        return sections
    
    async def process(self):
        
        file_extension = self.input_path.split(".")[-1]
        temp_path = f"temp/{self.input_path}"
        
        sections = None
        if file_extension == "txt" or file_extension == "doc":
            with open(temp_path, "r", encoding="utf-8") as file:
                content = file.read()
                sections = await self.extract_sections_from_txt_async(content)
        else:
            conv_res = doc_converter.convert(temp_path)
            doc = conv_res.document
            markdown = doc.export_to_markdown()
            sections = await self.extract_sections_async(markdown)
            
        for section in sections:
            section["file_path"] = self.input_path
            

        return sections
