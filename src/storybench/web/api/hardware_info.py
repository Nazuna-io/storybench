"""API endpoints for hardware information."""

import os
import logging
import psutil
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

import torch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hardware-info", tags=["hardware-info"])


@router.get("")
async def get_hardware_info() -> Dict[str, Any]:
    """Get information about available hardware."""
    try:
        info = {
            "gpu_available": torch.cuda.is_available(),
            "gpu_name": "",
            "vram_gb": 0,
            "cpu_cores": os.cpu_count() or 0,
            "ram_gb": 0
        }
        
        # Get RAM information
        try:
            mem = psutil.virtual_memory()
            info["ram_gb"] = mem.total / (1024**3)  # Convert to GB
        except Exception as e:
            logger.warning(f"Error getting RAM information: {str(e)}")
            
        # Get GPU information if available
        if info["gpu_available"]:
            try:
                device = torch.cuda.current_device()
                info["gpu_name"] = torch.cuda.get_device_name(device)
                info["vram_gb"] = torch.cuda.get_device_properties(device).total_memory / (1024**3)  # GB
            except Exception as e:
                logger.error(f"Error getting GPU information: {str(e)}")
                info["gpu_available"] = False
                
        return info
    except Exception as e:
        logger.error(f"Error getting hardware information: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
