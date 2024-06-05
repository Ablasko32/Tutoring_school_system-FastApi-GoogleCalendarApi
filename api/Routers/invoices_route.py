from typing import List

from fastapi import APIRouter, Query, status

from api.db.db_manager import db_dependancy
from api.db.models import Invoices

from .. import crud
from ..schemas import InvoiceData, InvoiceResponse, StudentResponse

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=InvoiceResponse
)
async def add_new_invoice(db: db_dependancy, invoice: InvoiceData):
    """Add new invoice to db using InvoiceData schema, returns item"""
    return await crud.add_item(db, invoice, Invoices)


@router.get(
    "/all", status_code=status.HTTP_200_OK, response_model=List[InvoiceResponse]
)
async def get_all_invoices(
    db: db_dependancy,
    payment_status: bool = None,
    invoice_date=None,
    page: int = Query(ge=1),
    limit: int = Query(10, gt=0),
):
    """Returns a list of invoices,filter by payment status, invoice date, pagination via page and limit parameters"""
    return await crud.get_all_invoices(db, page, limit, payment_status, invoice_date)


@router.put("/update", status_code=status.HTTP_201_CREATED)
async def update_invoice(
    db: db_dependancy, invoice: InvoiceData, id: int = Query(gt=0)
):
    """Update invoice model via ID, use InvoiceData schema"""
    return await crud.update_item(db, invoice, id, Invoices)


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(db: db_dependancy, id: int = Query(gt=0)):
    """Delete invoice via ID"""
    return await crud.delete_item(db, id, Invoices)


@router.get("/student", status_code=status.HTTP_200_OK, response_model=StudentResponse)
async def get_invoice_student(db: db_dependancy, id: int = Query(gt=0)):
    """Get student object linked to invoice via invoice ID"""
    return await crud.get_invoice_student(db, id)


@router.put(
    "/pay_invoice", status_code=status.HTTP_201_CREATED, response_model=InvoiceResponse
)
async def pay_student_invoice(db: db_dependancy, id: int = Query(gt=0)):
    """Mark student invoice as payed"""
    return await crud.pay_invoice(db, id)
