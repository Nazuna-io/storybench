"""Updated API endpoints for prompts management using MongoDB."""

from fastapi import APIRouter, HTTPException, Depends

from ..models.requests import PromptsUpdateRequest
from ..models.responses import PromptsResponse
from ...database.connection import get_database, init_database
from ...database.services.config_service import ConfigService


router = APIRouter()

# Dependency to get database config service
async def get_config_service() -> ConfigService:
    """Get database-backed config service instance."""
    try:
        # Try to get existing database connection first
        try:
            database = await get_database()
        except ConnectionError:
            # If no connection exists, initialize it
            database = await init_database()
            
        return ConfigService(database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize config service: {str(e)}")


@router.get("/prompts", response_model=PromptsResponse)
async def get_prompts():
    """Get current prompts configuration directly from Directus CMS."""
    from ...clients.directus_client import DirectusClient, DirectusClientError
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("🔄 API: Fetching fresh prompts directly from Directus CMS for frontend")
    
    try:
        directus_client = DirectusClient()
        fresh_prompts = await directus_client.fetch_prompts()
        
        if fresh_prompts and fresh_prompts.sequences:
            prompts_dict = {name: [{"name": prompt.name, "text": prompt.text} for prompt in prompt_list] 
                           for name, prompt_list in fresh_prompts.sequences.items()}
            
            response_data = {
                "prompts": prompts_dict,
                "version": fresh_prompts.version,
                "directus_id": fresh_prompts.directus_id,
                "created_at": fresh_prompts.created_at,
                "updated_at": fresh_prompts.updated_at
            }
            
            logger.info(f"✅ API: Successfully served {len(prompts_dict)} prompt sequences from Directus (version {fresh_prompts.version})")
            return response_data
        else:
            logger.error("❌ API: No published prompts found in Directus CMS")
            raise HTTPException(status_code=404, detail="No published prompts available in Directus CMS")
            
    except DirectusClientError as directus_error:
        logger.error(f"❌ API: Failed to fetch prompts from Directus: {directus_error}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch prompts from Directus: {directus_error}")
    except Exception as fetch_error:
        logger.error(f"❌ API: Unexpected error fetching prompts from Directus: {fetch_error}")
        raise HTTPException(status_code=500, detail=f"Prompt fetch failed: {fetch_error}")


@router.get("/sequences")
async def get_sequences():
    """Get available sequence names for prompts directly from Directus CMS."""
    from ...clients.directus_client import DirectusClient, DirectusClientError
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("🔄 API: Fetching sequence names directly from Directus CMS")
    
    try:
        directus_client = DirectusClient()
        fresh_prompts = await directus_client.fetch_prompts()
        
        if fresh_prompts and fresh_prompts.sequences:
            sequence_names = list(fresh_prompts.sequences.keys())
            logger.info(f"✅ API: Successfully served {len(sequence_names)} sequence names from Directus")
            return {"sequences": sequence_names}
        else:
            logger.error("❌ API: No published prompts found in Directus CMS")
            raise HTTPException(status_code=404, detail="No published prompts available in Directus CMS")
            
    except DirectusClientError as directus_error:
        logger.error(f"❌ API: Failed to fetch sequences from Directus: {directus_error}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch sequences from Directus: {directus_error}")
    except Exception as fetch_error:
        logger.error(f"❌ API: Unexpected error fetching sequences from Directus: {fetch_error}")
        raise HTTPException(status_code=500, detail=f"Sequence fetch failed: {fetch_error}")



@router.put("/prompts")
async def update_prompts(
    request: PromptsUpdateRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update prompts configuration in MongoDB."""
    try:
        # Save new configuration
        prompts_data = {"sequences": request.prompts}
        prompts_config = await config_service.save_prompts_config(prompts_data)
        
        response_data = {
            "prompts": {
                sequence_name: [prompt.model_dump() for prompt in prompt_list]
                for sequence_name, prompt_list in prompts_config.sequences.items()
            },
            "config_hash": prompts_config.config_hash,
            "version": prompts_config.version,
            "created_at": prompts_config.created_at.isoformat()
        }
        return PromptsResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save prompts: {str(e)}")
