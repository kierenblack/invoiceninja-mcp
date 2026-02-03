import requests
from typing import Literal
from .config import NINJA_URL, HEADERS


def register_tools(mcp):
    """Register all document-related tools with the MCP server (read-only)."""

    @mcp.tool()
    def get_documents(
        entity_type: Literal["invoices", "expenses", "projects", "tasks", "clients"],
        entity_id: str
    ) -> str:
        """
        List documents attached to an entity.
        - entity_type: Type of entity (invoices, expenses, projects, tasks, clients)
        - entity_id: The entity's hashed ID
        Returns list of attached documents with their details.
        """
        try:
            # Get the entity with documents included
            url = f"{NINJA_URL}/{entity_type}/{entity_id}?include=documents"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            entity = response.json().get('data', {})

            if not entity:
                return f"{entity_type[:-1].title()} {entity_id} not found."

            documents = entity.get('documents', [])

            if not documents:
                return f"No documents attached to this {entity_type[:-1]}."

            output = [f"--- Documents for {entity_type[:-1]} {entity_id} ---"]
            output.append(f"Total: {len(documents)} document(s)")
            output.append("")

            for doc in documents:
                doc_id = doc.get('id', 'N/A')
                name = doc.get('name', 'Unnamed')
                doc_type = doc.get('type', 'Unknown')
                size = doc.get('size', 0)

                # Convert size to human readable
                if size >= 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                elif size >= 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size} bytes"

                output.append(f"- {name}")
                output.append(f"  ID: {doc_id}")
                output.append(f"  Type: {doc_type} | Size: {size_str}")

            return "\n".join(output)
        except Exception as e:
            return f"Error fetching documents: {str(e)}"

    @mcp.tool()
    def get_document_details(document_id: str) -> str:
        """
        Get detailed information about a specific document.
        - document_id: The document's hashed ID
        """
        try:
            url = f"{NINJA_URL}/documents/{document_id}"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            doc = response.json().get('data', {})

            if not doc:
                return f"Document {document_id} not found."

            name = doc.get('name', 'Unnamed')
            doc_type = doc.get('type', 'Unknown')
            size = doc.get('size', 0)
            width = doc.get('width', 0)
            height = doc.get('height', 0)
            is_public = 'Yes' if doc.get('is_public') else 'No'
            created_at = doc.get('created_at', 'N/A')

            # Convert size
            if size >= 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size >= 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} bytes"

            output = [
                f"Document: {name}",
                f"- ID: {document_id}",
                f"- Type: {doc_type}",
                f"- Size: {size_str}",
            ]

            if width and height:
                output.append(f"- Dimensions: {width}x{height}")

            output.extend([
                f"- Public: {is_public}",
                f"- Created: {created_at}"
            ])

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def search_documents(search_term: str = "", limit: int = 20) -> str:
        """
        Search all documents across the system.
        - search_term: Optional text to search for in document names
        - limit: Maximum number of results
        """
        try:
            url = f"{NINJA_URL}/documents?per_page={limit}"
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            documents = response.json().get('data', [])

            if not documents:
                return "No documents found."

            # Filter by search term if provided
            if search_term:
                search_lower = search_term.lower()
                documents = [d for d in documents if search_lower in d.get('name', '').lower()]

            if not documents:
                return f"No documents matching '{search_term}'."

            output = [f"--- Found {len(documents)} Document(s) ---"]

            for doc in documents:
                doc_id = doc.get('id', 'N/A')
                name = doc.get('name', 'Unnamed')
                doc_type = doc.get('type', 'Unknown')
                size = doc.get('size', 0)

                if size >= 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                elif size >= 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size} bytes"

                output.append(f"- {name} (ID: {doc_id}) | {doc_type} | {size_str}")

            return "\n".join(output)
        except Exception as e:
            return f"Error: {str(e)}"
