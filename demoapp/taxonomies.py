from enum import StrEnum
from typing import Any, Dict, List

from django.db.models import TextChoices
from django.utils.translation import gettext as _


def serialize(klass) -> List[Dict[str, Any]]:
    return [
        {"name": x[1], "value": x[0]} for x in getattr(klass, "choices", [])
    ]


class GrnImageTag(TextChoices):
    DRIVER = "DRIVER", _("Driver")
    VEHICLE = "VEHICLE", _("Vehicle")
    DRIVER_LICENCE = "DRIVER_LICENCE", _("Driver Licence")


class InventoryMode(TextChoices):
    FIFO = "FIFO", _("First In - First Out")
    LIFO = "LIFO", _("Last In - First Out")


class TaxType(TextChoices):
    CGST = "CGST", _("CGST")
    SGST = "SGST", _("SGST")
    IGST = "IGST", _("IGST")
    UTGST = "UTGST", _("UTGST")
    CESS = "CESS", _("Cess")


class MaterialItem(TextChoices):
    PLASTIC = "PLASTIC", _("Plastic")
    GAS__AND_OIL = "GAS__AND_OIL", _("Gas & Oil")
    RUBBER = "RUBBER", _("Rubber")


class TradePartnerType(TextChoices):
    CUSTOMER = "CUSTOMER", _("Customer")
    VENDOR = "VENDOR", _("Vendor")


class KYCType(TextChoices):
    BASIC = "BASIC", _("Basic")
    VIDEO = "VIDEO", _("Video")


class KYCDocumentType(TextChoices):
    PAN = "PAN", _("Pan")
    AADHAAR = "AADHAAR", _("Aadhaar")
    VOTERID = "VOTERID", _("VoterId")


class DynamicEnumType(TextChoices):
    BANK_ACCOUNT_TYPE = "BANK_ACCOUNT_TYPE", _("Bank Account Type")
    BUSINESS_NATURE_CATEGORY = "BUSINESS_NATURE_CATEGORY", _(
        "Business Nature Category"
    )
    COA_CATEGORY = "COA_CATEGORY", _("Chart Of Account Category")
    COA_NATURE = "COA_NATURE", _("Chart Of Account Nature")
    COA_TYPE = "COA_TYPE", _("Chart Of Account Type")
    DEGREE = "DEGREE", _("Degree")
    DEPARTMENT_GROUP = "DEPARTMENT_GROUP", _("Department Group")
    DESIGNATION = "DESIGNATION", _("Designation")
    EPR_TYPE = "EPR_TYPE", _("EPR Type")
    FACTORY_LICENCE_ISSUING_AGENCY = "FACTORY_LICENCE_ISSUING_AGENCY", _(
        "Factory Licence Issuing Agency"
    )
    GENDER = "GENDER", _("Gender")
    INDUSTRY_CATEGORY = "INDUSTRY_CATEGORY", _("Industry Category")
    ITEM_CATEGORY = "ITEM_CATEGORY", _("Item Category")
    ITEM_LEVEL = "ITEM_LEVEL", _("Item Level")
    ITEM_NEXT_PROCESS = "ITEM_NEXT_PROCESS", _("Item Next Process")
    ITEM_STORAGE_TYPE = "ITEM_STORAGE_TYPE", _("Item Storage Type")
    MATERIAL_GENERATION = "MATERIAL_GENERATION", _("Material Generation")
    MATERIAL_SOURCE_NAME = "MATERIAL_SOURCE_NAME", _("Material Source Name")
    MATERIAL_TYPE = "MATERIAL_TYPE", _("Material Type")
    PAYMENT_TERM = "PAYMENT_TERM", _("Payment Term")
    QC_TYPE = "QC_TYPE", _("Quantity Check Type")
    SALUTATION = "SALUTATION", _("Salutation")
    VENDOR_GROUP = "VENDOR_GROUP", _("Vendor Group")


class EntityType(TextChoices):
    INDIVIDUAL = "INDIVIDUAL", _("Individual")
    PRIVATE = "PRIVATE", _("Private")
    PUBLIC = "PUBLIC", _("Public")
    LLP = "LLP", _("Limited Liability Partnership (LLP)")
    AOP = "AOP", _("Association of Persons (AOP)")
    PARTNERSHIP = "PARTNERSHIP", _("Partnership")
    NGO = "NGO", _("Non-governmental organization (NGO)")
    JOINT_VENTURE = "JOINT_VENTURE", _("Joint Venture")
    PROPRIETOR = "PROPRIETOR", _("Proprietor")


class MSMEType(TextChoices):
    MICRO = "MICRO", _("Micro Enterprise")
    SMALL = "SMALL", _("Small Enterprise")
    MEDIUM = "MEDIUM", _("Medium Enterprise")
    NA = "NA", _("Not Applicable")


class Status(TextChoices):
    DRAFT = "DRAFT", _("Draft")
    PENDING = "PENDING", _("Pending")
    CHANGE_REQUEST = "CHANGE_REQUEST", _("Change Request")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")


class AddressType(TextChoices):
    BILLING = "BILLING", _("Billing")
    SHIPPING = "SHIPPING", _("Shipping")
    NOTIFY_COPY = "NOTIFY_COPY", _("Notify Copy")
    CONSIGNEE = "CONSIGNEE", _("Consignee")


class IndiaGstSegment(TextChoices):
    WITHIN_STATE = "WITHIN_STATE", _("Within State")
    OUTSIDE_STATE = "OUTSIDE_STATE", _("Outside State")


class UserLocale(TextChoices):
    EN_IN = "en-IN", "India - English (en-IN)"


class SegregationSourceType(TextChoices):
    GRN_LINE_ITEM = "GRN_LINE_ITEM", "GRN Purchase"
    SEG_OUT = "SEG_OUT", "Previous Segregation"
    WT_RECEIPT_ENTRY = "WT_RECEIPT_ENTRY", "Warehouse Transfer Receipt Entry"


class WorkOrderType(TextChoices):
    INTERNAL = "INTERNAL", _("Internal")
    SALES = "SALES", _("Sales")


class InventoryLogSource(TextChoices):
    STORE = "STORE", "Store"
    PURCHASE = "PURCHASE", "Purchase"
    GRN = "GRN", "Good Receipt Note"
    SEGREGATION = "SEG", "Segregation"
    SEGREGATION_RETURN = "SEG_RET", "Segregation Return"
    PROCESS = "PROCESS", "Process"
    PACKAGING = "PACKAGING", "Packaging"
    DISPATCH = "DISPATCH", "Dispatch"


class InventoryLogDestination(TextChoices):
    STORE = "STORE", "Store"
    DISPATCH = "DISPATCH", "DISPATCH"
    SEGREGATION = "SEG", "Segregation"
    PROCESS = "PROCESS", "Process"
    PACKAGING = "PACKAGING", "Packaging"
    SALES = "SALES", "Sales"


class DispatchMode(TextChoices):
    HAND = "HAND", "Hand"
    ROAD = "ROAD", "Road"
    AIR = "AIR", "Air"


class TermType(TextChoices):
    DISPATCH = "DISPATCH", "Dispatch Order"
    PURCHASE_BILL = "PURCHASE_BILL", "Purchase Bill"
    SALES_ORDER = "SALES_ORDER", "Sales Order"
    SALES_INVOICE = "SALES_INVOICE", "Sales Invoice"
    PURCHASE_ORDER = "PURCHASE_ORDER", "Purchase Order"


class IncoTerm(TextChoices):
    EXW = "EXW", "Ex Works"
    FCA = "FCA", "Free Carrier"
    CPT = "CPT", "Carriage Paid To"
    CIP = "CIP", "Carriage and Insurance Paid To"
    DAP = "DAP", "Delivered at Place"
    DPU = "DPU", "Delivered at Place Unloaded"
    DDP = "DDP", "Delivered Duty Paid"
    FAS = "FAS", "Free Alongside Ship"
    FOB = "FOB", "Free on Board"
    CFR = "CFR", "Cost and Freight"
    CIF = "CIF", "Cost Insurance and Freight"


class AdjustmentType(TextChoices):
    PERCENT = "PERCENT", "Percent"
    VALUE = "VALUE", "Value"


class FactorQuestionType(TextChoices):
    SINGLE_CHOICE = "SINGLE_CHOICE", "Single Choice"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE", "Multiple Choice"
    RANGE = "RANGE", "Range"


class JobStatus(TextChoices):
    OPEN = "OPEN", "OPEN"
    PROCESSING = "PROCESSING", "PROCESSING"
    SUCCESS = "SUCCESS", "SUCCESS"
    FAIL = "FAIL", "FAIL"


class EmailReportType(TextChoices):
    PURCHASE_ADJUSTMENT_REPORT = (
        "Purchase Adjustment Report",
        "Purchase Adjustment Report",
    )


class UnitCategory(TextChoices):
    MASS = "MASS", _("Mass")
    VOLUME = "VOLUME", _("Volume")
    DISCRETE = "DISCRETE", _("Discrete")


class QuestionnaireType(TextChoices):
    PROCESS = "PROCESS", "Process"
    GRN = "GRN", "Grn"
    SEGREGATION = "SEGREGATION", "Segregation"
    BALING = "BALING", "Baling"
    PRODUCTION_BATCH = "PRODUCTION_BATCH", "Production Batch"


class LotInputType(TextChoices):
    BALE = "BALE", "Bale"
    LOT_OUTPUT = "LOT_OUTPUT", "Lot Output"
    NONE = "NONE", "None"


class WarehouseTransferEntryInputType(TextChoices):
    BALE = "BALE", "Bale"
    LOT_OUTPUT = "LOT_OUTPUT", "Lot Output"
    NONE = "NONE", "None"


class ItemOutputType(TextChoices):
    PLANNED = "PLANNED", "Planned"
    ADHOC = "ADHOC", "Adhoc"
    WASTAGE = "WASTAGE", "Wastage"
    BY_PRODUCT = "BY_PRODUCT", "By Product"


class StandardBillOfMaterialItemOutputType(TextChoices):
    PLANNED = "PLANNED", "Planned"
    WASTAGE = "WASTAGE", "Wastage"
    BY_PRODUCT = "BY_PRODUCT", "By Product"


class MachineStatus(TextChoices):
    OPERATIONAL = "OPERATIONAL", "Operational"
    NEEDS_MAINTAINANCE = "NEEDS_MAINTAINANCE", "Needs Maintainance"
    UNDER_MAINTAINANCE = "UNDER_MAINTAINANCE", "Under Maintainance"


class ProductionScheduleStatusType(TextChoices):
    STARTED = "STARTED", "Started"
    PAUSED = "PAUSED", "Paused"
    PENDING = "PENDING", "Pending"
    STOPPED = "STOPPED", "Stopped"


class QRCodeType(TextChoices):
    TPA = "TPA", "Trade Partner Address"
    GRN = "GRN", "Goods Receipt Note"
    GRN_LINE_ITEM = "GLI", "GRN Line Item"
    SEG = "SEG", "Segregation"
    SEG_OUT = "SGO", "Segregation Out"
    MRF_SEG = "MSG", "MRF Segregation"
    MRF_SEG_OUT = "MSO", "MRF Segregation Out"
    BALE_SET = "BLS", "Bale Set"
    BALE = "BAL", "Bale"
    DISPATCH_ORDER = "DSP", "Dispatch Order"
    DISPATCH_LINE_ITEM = "DLI", "Dispatch Line Item"
    BATCH_INPUT = "BIN", "Batch Input"
    BATCH_OUTPUT = "BOT", "Batch Output"
    PURCHASE_BILL = "PCB", "Purchase Bill"
    PURCHASE_ORDER = "PCO", "Purchase Order"
    SALES_ORDER = "SLO", "Sales Order"
    WORK_ORDER = "WOR", "Work Order"
    PRODUCTION = "PRN", "Production"
    SALES_BILL = "SLB", "Sales Bill"
    WAREHOUSE_TRANSFER = "WHT", "Warehouse Transfer"
    WAREHOUSE_TRANSFER_ENTRY = "WHE", "Warehouse Transfer Entry"
    WAREHOUSE_TRANSFER_RECEIPT = "WTR", "Warehouse Transfer RECEIPT"
    WAREHOUSE_TRANSFER_RECEIPT_ENTRY = (
        "WRE",
        "Warehouse Transfer Receipt Entry",
    )
    REJECT_HANDLING = "RHL", "Reject Handling"
    REJECT_HANDLING_LINE_ITEM = "RHI", "Reject Handling Line Item"
    REPACKING = "RPG", "Repacking"
    REPACKING_LINE_ITEM = "RPL", "Repacking Line Item"
    CHANGE_ITEM_GRADE_OUT = "CGO", "Change Item Grade Out"
    CHANGE_ITEM_GRADE = "CIG", "Change Item Grade"
    REPACKING_PACKAGING = "RPP", "Repacking Packaging"


class HttpMethod(TextChoices):
    GET = "GET", "Get"
    POST = "POST", "Post"


class RequestSessionKey(StrEnum):
    DEFAULT_ENTITY_FILTER = "__satmace_internal_default_entity_filter_id"


class DocumentType(TextChoices):
    GRN = "GoodsReceiptNote", "Goods Receipt Note"
    SEG = "Segregation", "Segregation"
    MRF_SEG = "MrfSegregation", "MRF Segregation"
    BALE_SET = "BaleSet", "Bale Set"
    DISPATCH_ORDER = "DispatchOrder", "Dispatch Order"
    PURCHASE_BILL = "PurchaseBill", "Purchase Bill"
    PURCHASE_ORDER = "PurchaseOrder", "Purchase Order"
    SALES_ORDER = "SalesOrder", "Sales Order"
    WORK_ORDER = "WorkOrder", "Work Order"
    PRODUCTION = "Production", "Production"
    SALES_BILL = "SalesBill", "Sales Bill"
    WAREHOUSE_TRANSFER = "WarehouseTransfer", "Warehouse Transfer"
    WAREHOUSE_TRANSFER_RECEIPT = (
        "WarehouseTransferReceipt",
        "Warehouse Transfer Receipt",
    )


class InventoryQueryType(TextChoices):
    GRN_APPROVAL = "GRN_APPROVAL", "GRN Approval"
    SEGREGATION_APPROVAL = "SEGREGATION_APPROVAL", "Segregation Approval"
    SEGREGATION_OUT_CREATE = (
        "SEGREGATION_LINE_ITEM_CREATE",
        "Segregation Line Item Create",
    )
    SEGREGATION_OUT_DELETE = (
        "SEGREGATION_LINE_ITEM_DELETE",
        "Segregation Line Item Delete",
    )
    BALE_CREATE = "BALE_CREATE", "Bale Create"
    BALE_DELETE = "BALE_DELETE", "Bale Delete"
    BALE_SET_APPROVAL = "BALE_SET_APPROVAL", "Bale Set Approval"
    DISPATCH_LINE_ITEM_CREATE = (
        "DISPATCH_LINE_ITEM_CREATE",
        "Dispatch Line Item Create",
    )
    DISPATCH_LINE_ITEM_DELETE = (
        "DISPATCH_LINE_ITEM_DELETE",
        "Dispatch Line Item Delete",
    )
    DISPATCH_ORDER_APPROVAL = (
        "DISPATCH_ORDER_APPROVAL",
        "Dispatch Order Approval",
    )
    BATCH_LOT_INPUT_CREATE = "BATCH_LOT_INPUT_CREATE", "Batch Lot Input Create"
    BATCH_LOT_INPUT_DELETE = "BATCH_LOT_INPUT_DELETE", "Batch Lot Input Delete"
    BATCH_LOT_OUTPUT_CREATE = (
        "BATCH_LOT_OUTPUT_CREATE",
        "Batch Lot Output Create",
    )
    BATCH_LOT_OUTPUT_DELETE = (
        "BATCH_LOT_OUTPUT_DELETE",
        "Batch Lot Output Delete",
    )
    PRODUCTION_APPROVAL = "PRODUCTION_APPROVAL", "Production Approval"
    WAREHOUSE_TRANSFER_ENTRY_CREATE = (
        "WAREHOUSE_TRANSFER_ENTRY_CREATE",
        "Warehouse Transfer Entry Create",
    )
    WAREHOUSE_TRANSFER_ENTRY_DELETE = (
        "WAREHOUSE_TRANSFER_ENTRY_DELETE",
        "Warehouse Transfer Entry Delete",
    )
    WAREHOUSE_TRANSFER_APPROVAL = (
        "WAREHOUSE_TRANSFER_APPROVAL",
        "Warehouse Transfer Approval",
    )
    WAREHOUSE_TRANSFER_RECEIPT_APPROVAL = (
        "WAREHOUSE_TRANSFER_RECEIPT_APPROVAL",
        "Warehouse Transfer Receipt Approval",
    )


class GSTTreatment(TextChoices):
    REGISTERED_BUSINESS_REGULAR = (
        "REGISTERED_BUSINESS_REGULAR",
        "Registered Business Regular",
    )
    REGISTERED_BUSINESS_COMPOSITION = (
        "REGISTERED_BUSINESS_COMPOSITION",
        "Registered Business Composition",
    )
    DEEMED_EXPORT = "DEEMED_EXPORT", "Deemed Export"
    SEZ_DEVELOPER = "SEZ_DEVELOPER", "Sez Developer"
    SPECIAL_ECONOMIC_ZONE = "SPECIAL_ECONOMIC_ZONE", "Special Economic Zone"
    UNREGISTERED_BUSINESS = "UNREGISTERED_BUSINESS", "Unregistered Business"


class TaskStatus(TextChoices):
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class RejectHandlingType(TextChoices):
    HANDLE_REJECT = "HANDLE_REJECT", "Handle Reject"
    CHANGE_ITEM_GRADE = "CHANGE_ITEM_GRADE", "Change Item Grade"


class QuestionType(TextChoices):
    FREE_TEXT = "FREE_TEXT", "Free Text"
    DROPDOWN = "DROPDOWN", "Dropdown"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE", "Multiple Choice"
    CHECKBOX = "CHECKBOX", "Checkbox"
    NUMERIC = "NUMERIC", "Numeric"


class BatchShiftType(TextChoices):
    DAY = "DAY", "Day"
    NIGHT = "NIGHT", "Night"


class UserAccountType(TextChoices):
    USER_ACCOUNT = "USER_ACCOUNT", "User Account"
    SUPER_ACCOUNT = "SUPER_ACCOUNT", "Super Account"
    MASTER_ACCOUNT = "MASTER_ACCOUNT", "Master Account"
