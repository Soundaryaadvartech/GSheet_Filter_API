import traceback
import json
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from fastapi.responses import JSONResponse
from database.database import get_db
from utilities.utlis import agg_grp
from utilities.generic_utils import get_dynamic_db, get_models
from pydantic import BaseModel
import asyncio
from pandas import DataFrame

router = APIRouter()


class FilterDataRequest(BaseModel):
    filter_dict: dict
    data_dict: dict
    groupby_dict: dict
async def run_in_thread(fn,*args):
    return await asyncio.to_thread(fn,*args)

@router.post("/aggregation/")
async def inventory_summary(business: str, filter_request: FilterDataRequest, db: Session = Depends(get_dynamic_db)):
    try:
        models = get_models(business)
        
        # Call the aggregation function and pass necessary arguments
        summary_df: DataFrame = await run_in_thread(agg_grp,db, models, business,
            filter_request.filter_dict,  # Filter for query
            filter_request.data_dict,  # Data aggregation methods
            filter_request.groupby_dict)  # Group-by conditions

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content = json.loads(summary_df.to_json(orient="records"))
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Something went wrong", "error": str(e)}
        )

    

    

