import traceback
import json
from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException
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

UNIQUE_COLUMN_MAPPINGS = {
    "zing": ["Item_Name", "Item_Type", "Category","Is_Public", "Colour", "__Batch", "Fabric", "Fit", 
                    "Neck", "Occasion", "Print", "Size", "Sleeve", "Mood", "__Details", "__Print_Type", 
                    "__Quadrant", "__Style_Type"],
    
    "prathiksham": ["Item_Name", "Item_Type", "Category", "Colour", "__Batch", "Is_Public","Fabric", "Fit", "Lining", 
             "Neck", "Occasion", "Print", "Product_Availability", "Size", "Sleeve", "Pack","Bottom_Length", 
             "Bottom_Print", "Bottom_Type", "Collections", "Details", "Pocket", "Top_Length", "Waist_Band"] ,
    
    "beelittle" : [
        "Item_Name", "Item_Type", "Is_Public","Age", "Bottom","Bundles","Gender","Pack_Size","Pattern","Sale","Size",
        "Sleeve","Style","Top","Weight","Width","__Season","Colour", "Fabric", "Pattern", "Product_Type", 
        "Weave_Type", "Print_Colour", "Print_Size", "Print_Theme", "Print_Style", "Print Key Motif",
    ]
}

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

@router.get("/unique_values")
def unique_values(business: str, db: Session = Depends(get_db)):
    try:
        models = get_models(business)  # Load the correct SQLAlchemy models
        Item = models.Item  # Access the Item model dynamically

        if business not in UNIQUE_COLUMN_MAPPINGS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid business name")

        # Get the column names specific to the business
        selected_columns = UNIQUE_COLUMN_MAPPINGS[business]

        unique_values = {}
        
        for column_name in selected_columns:
            column_attr = getattr(Item, column_name, None)  # Dynamically get column attribute
            if column_attr is not None:
                unique_values[column_name] = [
                    row[0] for row in db.query(distinct(column_attr)).all() if row[0] is not None
                ]

        return JSONResponse(status_code=status.HTTP_200_OK, content=unique_values)
    
    except HTTPException as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=e.status_code,
            content = e.detail )

    except Exception:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"message": "Something Went Wrong"}
        )



