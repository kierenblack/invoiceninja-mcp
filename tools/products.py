import requests
from .config import NINJA_URL, HEADERS


def register_tools(mcp):
    """Register all product-related tools with the MCP server."""

    @mcp.tool()
    def get_products(limit: int = 50) -> str:
        """Fetch and list all products/services available in Invoice Ninja."""
        try:
            response = requests.get(f"{NINJA_URL}/products?per_page={limit}", headers=HEADERS)
            response.raise_for_status()
            products = response.json().get('data', [])

            if not products:
                return "No products/services found."

            output = [f"--- Found {len(products)} Products/Services ---"]
            for prod in products:
                prod_id = prod.get('id')
                name = prod.get('product_key', 'N/A')
                price = prod.get('price', 0.0)
                output.append(f"- {name} (ID: {prod_id}): ${price}")

            return "\n".join(output)
        except Exception as e:
            return f"Error fetching products: {str(e)}"
