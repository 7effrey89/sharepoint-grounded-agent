# sharepoint grounded copilot
Sharepoint grounded copilot. azure function to provide custom skillset to fill field in index.

1) This demo extracts sharepoint content through microsoft graph. 
2) The content is then landed as .json blobs in a blob storage account where a blob indexer from AI search will ingest all new/modified files.
3) A azure sql database is used as a watermark table to keep track of which sharepoint pages have been modied since the last time the AI search index was updated. 

The search index includes fields that contains meta data from the sharepoint pages, and is being populated by a custom skillset in AI search through an Azure Function.

The chat portal is made in streamlit

# Architecture:
![image](https://github.com/user-attachments/assets/d2d15f32-62c4-4d75-9a3d-76f6f560f8c2)

# Solution screenshot:
<img width="512" alt="image" src="https://github.com/user-attachments/assets/1ae2fadf-bbe8-44a1-b30c-2b6a35d9aada">

# Sharepoint: 
Agent is grounded on information from sharepoint pages (.aspx):

The example sharepoint pages used looks like below. Tags and other relavant metadata associated with the sharepoint pages were located at the right side of each page. These have been populated as additional "metadata" fields in the AI Search index to enable user to filter and narrow the scope of their Agents, but also giving it more context for more accurate information retrieval. 
![image](https://github.com/user-attachments/assets/71582c55-acf4-4195-97a8-3b0d9299a3f8)
