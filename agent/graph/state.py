from typing import Optional
from typing_extensions import TypedDict
from pydantic import BaseModel

class ProjectContext(BaseModel):
  framework: str                  
  main_file: str                  
  routes_files: list[str]         
  has_existing_middleware: bool   
  route_summary: list[str]        


class AgentState(TypedDict):
  target_path: str                        
  project_context: Optional[ProjectContext]
  main_file_content : Optional[str]
  generated_middleware: Optional[str]     
  generated_tests: Optional[str]  
  modified_main: Optional[str]        
  validation_result: Optional[str]        
  validation_feedback: Optional[str]      
  revision_count: int                     
  error: Optional[str]           