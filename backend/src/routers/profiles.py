"""Evaluation profile endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from src.db.session import get_session
from src.db.models import EvaluationProfile, ModelConfig
from src.schemas.base import EvaluationProfileCreate, EvaluationProfileUpdate, EvaluationProfileResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/profiles", response_model=EvaluationProfileResponse, tags=["Profiles"])
async def create_profile(
    profile: EvaluationProfileCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new evaluation profile."""
    try:
        # Verify model_config exists
        result = await session.execute(
            select(ModelConfig).where(ModelConfig.id == profile.model_config_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Model config not found")
        
        db_profile = EvaluationProfile(
            name=profile.name,
            description=profile.description,
            model_config_id=profile.model_config_id,
            single_weights=profile.single_weights,
            conversational_weights=profile.conversational_weights
        )
        session.add(db_profile)
        await session.commit()
        await session.refresh(db_profile)
        
        logger.info(f"Created evaluation profile: {db_profile.id} ({profile.name})")
        return db_profile
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profiles", response_model=list[EvaluationProfileResponse], tags=["Profiles"])
async def list_profiles(session: AsyncSession = Depends(get_session)):
    """List all evaluation profiles."""
    try:
        result = await session.execute(select(EvaluationProfile))
        profiles = result.scalars().all()
        return profiles
    except Exception as e:
        logger.error(f"Error listing profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_id}", response_model=EvaluationProfileResponse, tags=["Profiles"])
async def get_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific evaluation profile."""
    try:
        result = await session.execute(
            select(EvaluationProfile).where(EvaluationProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profiles/{profile_id}", response_model=EvaluationProfileResponse, tags=["Profiles"])
async def update_profile(
    profile_id: int,
    profile: EvaluationProfileUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update an evaluation profile."""
    try:
        result = await session.execute(
            select(EvaluationProfile).where(EvaluationProfile.id == profile_id)
        )
        db_profile = result.scalar_one_or_none()
        
        if not db_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Verify model_config if updating
        if profile.model_config_id is not None:
            config_result = await session.execute(
                select(ModelConfig).where(ModelConfig.id == profile.model_config_id)
            )
            if not config_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Model config not found")
            db_profile.model_config_id = profile.model_config_id
        
        # Update fields if provided
        if profile.name is not None:
            db_profile.name = profile.name
        if profile.description is not None:
            db_profile.description = profile.description
        if profile.single_weights is not None:
            db_profile.single_weights = profile.single_weights
        if profile.conversational_weights is not None:
            db_profile.conversational_weights = profile.conversational_weights
        
        await session.commit()
        await session.refresh(db_profile)
        
        logger.info(f"Updated profile: {profile_id}")
        return db_profile
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/profiles/{profile_id}", tags=["Profiles"])
async def delete_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete an evaluation profile."""
    try:
        result = await session.execute(
            select(EvaluationProfile).where(EvaluationProfile.id == profile_id)
        )
        db_profile = result.scalar_one_or_none()
        
        if not db_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        await session.delete(db_profile)
        await session.commit()
        
        logger.info(f"Deleted profile: {profile_id}")
        return {"status": "deleted", "id": profile_id}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
