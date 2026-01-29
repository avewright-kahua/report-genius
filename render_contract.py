"""Script to query a contract and render it with the portable view template."""
import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import httpx

QUERY_URL = 'https://demo01service.kahua.com/v2/domains/Summit/projects/0/query?returnDefaultAttributes=true'
AUTH = os.getenv('KAHUA_BASIC_AUTH')
if AUTH and not AUTH.startswith('Basic '):
    AUTH = f'Basic {AUTH}'

async def get_contract():
    """Query a contract from Kahua."""
    query = {
        'sets': [{
            'name': 'contracts',
            'entityDef': 'kahua_Contract.Contract',
            'conditions': [],
            'maxEntities': 1
        }]
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            QUERY_URL, 
            json=query, 
            headers={'Content-Type': 'application/json', 'Authorization': AUTH}
        )
        print(f"Response status: {resp.status_code}")
        data = resp.json()
        print(f"Response keys: {data.keys()}")
        if 'sets' in data:
            print(f"Sets: {len(data['sets'])}")
            for s in data['sets']:
                print(f"  Set '{s.get('name')}': {len(s.get('entities', []))} entities")
        return data

def render_template(template_id: str, entity_data: dict):
    """Render the template with entity data."""
    from pv_template_schema import PortableTemplate
    from pv_template_renderer import TemplateRenderer
    
    # Load template
    template_path = Path(__file__).parent / "pv_templates" / "saved" / f"{template_id}.json"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    with open(template_path, 'r') as f:
        template = PortableTemplate.from_json(f.read())
    
    # Extract entity from wrapped format
    if isinstance(entity_data, dict):
        if "sets" in entity_data and isinstance(entity_data["sets"], list):
            for s in entity_data["sets"]:
                if isinstance(s.get("entities"), list) and s["entities"]:
                    entity_data = s["entities"][0]
                    break
        elif "entities" in entity_data and isinstance(entity_data["entities"], list):
            if entity_data["entities"]:
                entity_data = entity_data["entities"][0]
    
    # Render
    renderer = TemplateRenderer()
    output_path, doc_bytes = renderer.render(template, entity_data)
    
    return output_path, len(doc_bytes)

async def main():
    print("Querying contract from Kahua...")
    data = await get_contract()
    
    # Handle both response formats
    entities = []
    if data.get('sets') and data['sets'][0].get('entities'):
        entities = data['sets'][0]['entities']
    elif data.get('entities'):
        entities = data['entities']
    
    if entities:
        c = entities[0]
        print(f"\nContract found:")
        print(f"  Number: {c.get('Number')}")
        print(f"  Description: {c.get('Description')}")
        print(f"  Contractor: {c.get('ContractorCompany', {}).get('ShortLabel') if c.get('ContractorCompany') else 'N/A'}")
        print(f"  Status: {c.get('WorkflowStatus')}")
        print(f"  Pending Value: {c.get('ContractPendingTotalValue')}")
        
        # Save for debugging
        with open('contract_data.json', 'w') as f:
            json.dump(c, f, indent=2)
        print(f"  (Full data saved to contract_data.json)")
    else:
        print("No contracts found!")
        return
    
    print("\nRendering with template 'pv-detailed-contract'...")
    try:
        # Pass the entity directly, not wrapped
        output_path, size = render_template("pv-detailed-contract", {"entities": entities})
        print(f"\n✓ Document generated!")
        print(f"  File: {output_path}")
        print(f"  Size: {size:,} bytes")
        print(f"  Download URL: http://localhost:8000/reports/{output_path.name}")
    except Exception as e:
        print(f"\n✗ Rendering failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
