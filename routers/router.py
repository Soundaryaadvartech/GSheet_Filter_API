import traceback
import json
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from fastapi.responses import JSONResponse
from database.database import get_db,get_business_name
from utilities.utlis import agg_grp
from utilities.generic_utils import get_dynamic_db, get_models
from pydantic import BaseModel
import asyncio
from pandas import DataFrame
from io import StringIO
from fastapi.responses import StreamingResponse
from utilities.filtered_data import get_filter_data
from utilities.columns_to_choose import get_column_names


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
        business = get_business_name(business)
        
        # Call the aggregation function and pass necessary arguments
        summary_df: DataFrame = await run_in_thread(agg_grp,db, models, business,
            filter_request.filter_dict,  # Filter for query
            filter_request.data_dict,  # Data aggregation methods
            filter_request.groupby_dict)  # Group-by conditions

        
        csv_buffer = StringIO()
        summary_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        return StreamingResponse(csv_buffer, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=inventory_summary.csv"})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Something went wrong", "error": str(e)}
        )

@router.post("/get_filter_data")
async def get_table(business: str, db: Session = Depends(get_dynamic_db)):
    try:
        print(f"Fetching filter data for business: {business}")  # Log business name
        print(business)
        models = get_models(business)
        business = get_business_name(business)
        print(f"Using models: {models}")  # Log models
        filter_data = await run_in_thread(get_filter_data, db, models, business)

        if filter_data.empty:  
            print("No data found!")  # Log empty response
            return JSONResponse(status_code=204, content={"message": "No data available"})

        print("Data fetched successfully!")  # Log success

        csv_buffer = StringIO()
        filter_data.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        return StreamingResponse(csv_buffer, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=filter_data.csv"})

    except Exception as e:
        print(f"Error occurred: {e}")  # Log errors
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": "Something went wrong"})
    
@router.post("/get_column_names")
async def get_table(business: str, db: Session = Depends(get_dynamic_db)):
    try:
        print(f"Fetching filter data for business: {business}")  # Log business name
        
        models = get_models(business)
        print(f"Using models: {models}")  # Log models
        business = get_business_name(business)
        column_name = await run_in_thread(get_column_names, db, models, business)

        if column_name.empty:  
            print("No data found!")  # Log empty response
            return JSONResponse(status_code=204, content={"message": "No data available"})

        print("Data fetched successfully!")  # Log success

        csv_buffer = StringIO()
        column_name.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        return StreamingResponse(csv_buffer, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=column_name.csv"})

    except Exception as e:
        print(f"Error occurred: {e}")  # Log errors
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": "Something went wrong"})

    

