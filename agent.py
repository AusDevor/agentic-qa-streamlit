from smolagents import LiteLLMModel, Tool
from smolagents.agents import CodeAgent
import os

class TableOfContentRetriever(Tool):
    name = "table_of_content_retriever"
    description = (
        "Retrieves all section list within document"
    )
    inputs = {
    }
    output_type = "array"

    def __init__(self, sections, **kwargs):
        super().__init__(**kwargs)
        self.sections = sections

    def forward(self) -> str:
      result = ""
      for i in range(len(self.sections)):
        section = self.sections[i]
        result += f"==========Section {str(i)}===========\n"
        result += f"Section Title:{section['title']}, start_index:{section['start_index']}, length:{section['length']}, summary:{section['summary']}\n"
        # print ('*********************', section['summary'])
        #result += f"Section Summary:{section['summary']}\n"

      return result

class SectionTextRetriever(Tool):
    name = "section_text_retriever"
    description = (
          "Retrieves full section text by section index"
    )
    inputs = {
        "indices": {
            "type": "array",
            "description": "The section index to retrieve",
        }
    }
    output_type = "array"

    def __init__(self, sections, **kwargs):
      super().__init__(**kwargs)
      self.sections = sections

    def forward(self, indices):
      return [self.sections[index]['text'] for index in indices]


api_key = os.getenv("OPENAI_API_KEY")
model = LiteLLMModel(
    model_id="gpt-4o",
    api_key=api_key
)

class DocQAAgent:
    
    def __init__(self):
        pass

    def setSections(self, sections):
        self.toc_retriever = TableOfContentRetriever(sections)
        self.section_retriever = SectionTextRetriever(sections)
        self.sections = sections
        
        self.agent = CodeAgent(
            tools=[self.toc_retriever, self.section_retriever],
            model=model,
            max_steps=5,
            verbosity_level=2,
            additional_authorized_imports=['matplotlib', 'numpy'],
        )
    
    def run(self, query):
        agent_output = self.agent.run(query)
        return agent_output
