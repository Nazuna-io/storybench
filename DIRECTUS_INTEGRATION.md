# Directus CMS Integration

This module provides integration between the storybench system and Directus CMS for managing prompts. The Directus CMS replaces the MongoDB-based prompt management, allowing for easier content management through a web interface.

## Features

- ✅ Fetch prompts from Directus CMS with filtering by publication status
- ✅ Support for versioned prompt sets
- ✅ Automatic conversion to storybench MongoDB format
- ✅ CLI commands for easy synchronization
- ✅ Comprehensive error handling and retries
- ✅ Unit and integration tests
- ✅ Long timeout support for serverless Directus instances

## Architecture

### Components

1. **DirectusClient** - HTTP client for interacting with Directus API
2. **DirectusModels** - Pydantic models matching Directus schema
3. **DirectusIntegrationService** - High-level service for syncing data
4. **CLI Commands** - Command-line interface for management

### Data Flow

```
Directus CMS → DirectusClient → DirectusIntegrationService → MongoDB
```

## Configuration

Add these environment variables:

```bash
DIRECTUS_URL=https://your-directus-instance.com
DIRECTUS_TOKEN=your_static_api_token
```

## Usage

### CLI Commands

Sync latest published prompts:
```bash
python -m src.storybench.cli sync-prompts
```

List available versions:
```bash
python -m src.storybench.cli sync-prompts --list-versions
```

Sync specific version:
```bash
python -m src.storybench.cli sync-prompts --version 1
```

Test connection:
```bash
python -m src.storybench.cli sync-prompts --test-connection
```

### Programmatic Usage

```python
from storybench.clients.directus_client import DirectusClient
from storybench.database.services.directus_integration_service import DirectusIntegrationService

# Initialize client
client = DirectusClient()

# Test connection
is_connected = await client.test_connection()

# Fetch latest prompts
prompts = await client.fetch_prompts()

# Use integration service for full MongoDB sync
service = DirectusIntegrationService(database, client)
synced_prompts = await service.sync_prompts_from_directus()
```

## Schema Structure

The Directus schema uses a many-to-many relationship structure:

- **prompt_set_versions** - Versioned collections of prompt sequences
- **prompt_sequences** - Named sequences of related prompts  
- **prompts** - Individual prompt content
- Junction tables for relationships

### Key Fields

**PromptSetVersion:**
- `version_number` - Numeric version identifier
- `version_name` - Human-readable name
- `status` - Publication status (draft/published/archived)
- `description` - Version description

**PromptSequence:**
- `sequence_name` - Unique sequence identifier
- `sequence_description` - Description of the sequence purpose
- `status` - Publication status

**Prompt:**
- `name` - Prompt identifier
- `text` - The actual prompt content
- `order_in_sequence` - Ordering within sequence
- `status` - Publication status

## Error Handling

The client includes comprehensive error handling:

- **DirectusAuthenticationError** - Invalid/expired tokens
- **DirectusNotFoundError** - Missing resources
- **DirectusServerError** - Server-side issues
- **DirectusClientError** - General API failures

Timeouts are set to 60 seconds by default to accommodate serverless spinup times.

## Testing

Run unit tests:
```bash
pytest tests/clients/test_directus_client.py -v
```

Run integration tests (requires live Directus instance):
```bash
pytest tests/clients/test_directus_integration.py -v
```

Run standalone integration test:
```bash
python test_directus_integration.py
```

## Data Conversion

The system automatically converts from Directus nested structure to the flat MongoDB format used by storybench:

**Directus Format (nested):**
```json
{
  "sequences_in_set": [
    {
      "prompt_sequences_id": {
        "sequence_name": "FilmNarrative",
        "prompts_in_sequence": [
          {
            "prompts_id": {
              "name": "concept",
              "text": "Create a film concept..."
            }
          }
        ]
      }
    }
  ]
}
```

**MongoDB Format (flat):**
```json
{
  "sequences": {
    "FilmNarrative": [
      {
        "name": "concept",
        "text": "Create a film concept..."
      }
    ]
  }
}
```

## Development

### Adding New Fields

1. Update the Pydantic models in `directus_models.py`
2. Update the conversion logic in `DirectusClient.convert_to_storybench_format()`
3. Add tests for the new fields
4. Update API field queries if needed

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

The client includes detailed error messages and supports inspection of the full API response structure.
