from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

from apps.accounts.models import CustomUser, AuditLog
from apps.bom.models import RawMaterial, Product, BillOfMaterial, BOMItem
from apps.orders.models import Customer, SalesOrder, SalesOrderItem
from apps.procurement.models import Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, VendorCommunication
from apps.invoices.models import Invoice, InvoiceItem
from apps.payments.models import Payment

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds realistic manufacturing data for OrderCraft ERP presentation'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING(">> Seeding OrderCraft ERP manufacturing data..."))

        # 1. Users & Roles (Module 7: RBAC)
        users_data = [
            {
                'username': 'admin',
                'first_name': 'Vikram',
                'last_name': 'Malhotra',
                'email': 'admin@ordercraft.com',
                'role': 'ADMIN',
                'department': 'Plant Executive Management',
                'designation': 'Plant General Manager',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'sales_officer',
                'first_name': 'Rohan',
                'last_name': 'Verma',
                'email': 'sales@ordercraft.com',
                'role': 'SALES',
                'department': 'Sales & Commercial Operations',
                'designation': 'Senior Sales Engineer',
            },
            {
                'username': 'prod_manager',
                'first_name': 'Anil',
                'last_name': 'Deshmukh',
                'email': 'production@ordercraft.com',
                'role': 'PRODUCTION',
                'department': 'Manufacturing Operations',
                'designation': 'Production & Quality Manager',
            },
            {
                'username': 'proc_officer',
                'first_name': 'Pooja',
                'last_name': 'Nair',
                'email': 'procurement@ordercraft.com',
                'role': 'PROCUREMENT',
                'department': 'Supply Chain & Sourcing',
                'designation': 'Lead Procurement Specialist',
            },
            {
                'username': 'accountant',
                'first_name': 'Suresh',
                'last_name': 'Iyer',
                'email': 'finance@ordercraft.com',
                'role': 'FINANCE',
                'department': 'Finance & Commercial Accounts',
                'designation': 'Chief Financial Controller',
            },
        ]

        created_users = {}
        for u in users_data:
            user, created = CustomUser.objects.get_or_create(
                username=u['username'],
                defaults={
                    'first_name': u['first_name'],
                    'last_name': u['last_name'],
                    'email': u['email'],
                    'role': u['role'],
                    'department': u['department'],
                    'designation': u['designation'],
                    'is_staff': u.get('is_staff', False),
                    'is_superuser': u.get('is_superuser', False),
                }
            )
            user.set_password('ordercraft123')
            user.save()
            created_users[u['username']] = user

        admin_user = created_users['admin']

        # 2. Raw Materials (Module 2: BOM)
        raw_materials_data = [
            {'code': 'RM-STL-001', 'name': 'Cold Rolled Steel Sheet 2.5mm', 'category': 'METALS', 'unit_of_measure': 'KG', 'standard_cost': Decimal('85.00'), 'current_stock': Decimal('450.00'), 'reorder_level': Decimal('200.00'), 'warehouse_location': 'Bay A, Rack 01'},
            {'code': 'RM-COP-002', 'name': 'Electrolytic Copper Winding Wire 1.2mm', 'category': 'ELECTRICAL', 'unit_of_measure': 'KG', 'standard_cost': Decimal('780.00'), 'current_stock': Decimal('85.00'), 'reorder_level': Decimal('100.00'), 'warehouse_location': 'Bay E, Cabinet 03'},  # LOW STOCK
            {'code': 'RM-CAST-003', 'name': 'Cast Iron Motor Casing FG260', 'category': 'METALS', 'unit_of_measure': 'PCS', 'standard_cost': Decimal('1450.00'), 'current_stock': Decimal('35.00'), 'reorder_level': Decimal('20.00'), 'warehouse_location': 'Yard Heavy Staging'},
            {'code': 'RM-BRG-004', 'name': 'Deep Groove Ball Bearing 6205-2RS', 'category': 'FASTENERS', 'unit_of_measure': 'PCS', 'standard_cost': Decimal('320.00'), 'current_stock': Decimal('120.00'), 'reorder_level': Decimal('50.00'), 'warehouse_location': 'Bay F, Shelf 12'},
            {'code': 'RM-ROTOR-005', 'name': 'Dynamically Balanced Rotor Shaft 45C8', 'category': 'METALS', 'unit_of_measure': 'PCS', 'standard_cost': Decimal('1850.00'), 'current_stock': Decimal('18.00'), 'reorder_level': Decimal('25.00'), 'warehouse_location': 'Bay B, Rack 04'}, # LOW STOCK
            {'code': 'RM-POLY-006', 'name': 'Nitrile Rubber Oil Seal & O-Ring Kit', 'category': 'POLYMERS', 'unit_of_measure': 'SET', 'standard_cost': Decimal('140.00'), 'current_stock': Decimal('250.00'), 'reorder_level': Decimal('60.00'), 'warehouse_location': 'Bay D, Bin 18'},
            {'code': 'RM-CHM-007', 'name': 'Epoxy Anti-Corrosive Industrial Primer', 'category': 'CHEMICALS', 'unit_of_measure': 'LTR', 'standard_cost': Decimal('420.00'), 'current_stock': Decimal('65.00'), 'reorder_level': Decimal('30.00'), 'warehouse_location': 'Flammable Store 01'},
            {'code': 'RM-GEAR-008', 'name': 'Hardened Alloy Pinion Gear 18T', 'category': 'METALS', 'unit_of_measure': 'PCS', 'standard_cost': Decimal('2400.00'), 'current_stock': Decimal('15.00'), 'reorder_level': Decimal('20.00'), 'warehouse_location': 'Bay C, Rack 08'}, # LOW STOCK
            {'code': 'RM-IMP-009', 'name': 'Bronze Radial Impeller 200mm', 'category': 'METALS', 'unit_of_measure': 'PCS', 'standard_cost': Decimal('3200.00'), 'current_stock': Decimal('22.00'), 'reorder_level': Decimal('15.00'), 'warehouse_location': 'Bay C, Rack 09'},
        ]

        rms = {}
        for rm_item in raw_materials_data:
            rm, _ = RawMaterial.objects.update_or_create(
                code=rm_item['code'],
                defaults=rm_item
            )
            rms[rm.code] = rm

        # 3. Finished Products (Module 2: BOM)
        products_data = [
            {
                'product_code': 'FG-MTR-5HP',
                'name': '5HP Three-Phase TEFC Induction Motor (415V, 1440 RPM)',
                'category': 'Industrial Motors',
                'description': 'Heavy duty cast iron foot mounted motor with IP55 protection for continuous pump & conveyor drives.',
                'selling_price': Decimal('24500.00'),
                'lead_time_days': 4,
            },
            {
                'product_code': 'FG-GEAR-01',
                'name': 'High-Torque Inline Helical Reduction Gearbox (Ratio 1:15)',
                'category': 'Transmission Systems',
                'description': 'Case hardened alloy steel gears with synthetic oil lubrication for mining and crushers.',
                'selling_price': Decimal('38000.00'),
                'lead_time_days': 6,
            },
            {
                'product_code': 'FG-PUMP-10HP',
                'name': 'Centrifugal End-Suction Process Water Pump 10HP',
                'category': 'Industrial Pumps',
                'description': 'High volume water pump with bronze impeller and mechanical gland packing for chemical and boiler feeds.',
                'selling_price': Decimal('42500.00'),
                'lead_time_days': 5,
            },
        ]

        prods = {}
        for p_item in products_data:
            p, _ = Product.objects.update_or_create(
                product_code=p_item['product_code'],
                defaults=p_item
            )
            prods[p.product_code] = p

        # 4. Bill of Materials Recipes (Module 2: BOM)
        # BOM for 5HP Motor
        bom1, _ = BillOfMaterial.objects.update_or_create(
            product=prods['FG-MTR-5HP'],
            defaults={
                'bom_number': 'BOM-2026-0001',
                'version': 'v2.1',
                'is_approved': True,
                'approved_by': created_users['prod_manager'],
                'notes': 'Standard industrial production BOM compliant with IS:12615 energy efficiency standard.'
            }
        )
        BOMItem.objects.update_or_create(
            bom=bom1, raw_material=rms['RM-CAST-003'],
            defaults={'quantity_required': Decimal('1.00'), 'wastage_percentage': Decimal('0.00'), 'notes': 'Main frame'}
        )
        BOMItem.objects.update_or_create(
            bom=bom1, raw_material=rms['RM-ROTOR-005'],
            defaults={'quantity_required': Decimal('1.00'), 'wastage_percentage': Decimal('1.00'), 'notes': 'Rotor assembly'}
        )
        BOMItem.objects.update_or_create(
            bom=bom1, raw_material=rms['RM-COP-002'],
            defaults={'quantity_required': Decimal('4.80'), 'wastage_percentage': Decimal('3.50'), 'notes': 'Stator winding coil'}
        )
        BOMItem.objects.update_or_create(
            bom=bom1, raw_material=rms['RM-BRG-004'],
            defaults={'quantity_required': Decimal('2.00'), 'wastage_percentage': Decimal('0.00'), 'notes': 'Drive and non-drive end'}
        )
        BOMItem.objects.update_or_create(
            bom=bom1, raw_material=rms['RM-POLY-006'],
            defaults={'quantity_required': Decimal('1.00'), 'wastage_percentage': Decimal('0.00'), 'notes': 'IP55 sealing'}
        )
        BOMItem.objects.update_or_create(
            bom=bom1, raw_material=rms['RM-CHM-007'],
            defaults={'quantity_required': Decimal('0.75'), 'wastage_percentage': Decimal('5.00'), 'notes': 'Exterior machine paint'}
        )

        # BOM for Helical Gearbox
        bom2, _ = BillOfMaterial.objects.update_or_create(
            product=prods['FG-GEAR-01'],
            defaults={
                'bom_number': 'BOM-2026-0002',
                'version': 'v1.4',
                'is_approved': True,
                'approved_by': created_users['prod_manager'],
                'notes': 'Heavy duty transmission gearbox BOM with case-hardened alloy gearing.'
            }
        )
        BOMItem.objects.update_or_create(
            bom=bom2, raw_material=rms['RM-CAST-003'],
            defaults={'quantity_required': Decimal('1.00'), 'wastage_percentage': Decimal('0.00'), 'notes': 'Gearbox housing'}
        )
        BOMItem.objects.update_or_create(
            bom=bom2, raw_material=rms['RM-GEAR-008'],
            defaults={'quantity_required': Decimal('4.00'), 'wastage_percentage': Decimal('2.00'), 'notes': 'Helical gear set'}
        )
        BOMItem.objects.update_or_create(
            bom=bom2, raw_material=rms['RM-BRG-004'],
            defaults={'quantity_required': Decimal('4.00'), 'wastage_percentage': Decimal('0.00'), 'notes': 'Shaft support bearings'}
        )
        BOMItem.objects.update_or_create(
            bom=bom2, raw_material=rms['RM-POLY-006'],
            defaults={'quantity_required': Decimal('2.00'), 'wastage_percentage': Decimal('0.00'), 'notes': 'Shaft oil seals'}
        )

        # BOM for Pump
        bom3, _ = BillOfMaterial.objects.update_or_create(
            product=prods['FG-PUMP-10HP'],
            defaults={
                'bom_number': 'BOM-2026-0003',
                'version': 'v1.0',
                'is_approved': True,
                'approved_by': created_users['prod_manager'],
                'notes': 'Chemical and high-pressure process pump BOM.'
            }
        )
        BOMItem.objects.update_or_create(
            bom=bom3, raw_material=rms['RM-CAST-003'],
            defaults={'quantity_required': Decimal('1.00'), 'wastage_percentage': Decimal('0.00'), 'notes': 'Volute casing'}
        )
        BOMItem.objects.update_or_create(
            bom=bom3, raw_material=rms['RM-IMP-009'],
            defaults={'quantity_required': Decimal('1.00'), 'wastage_percentage': Decimal('0.00'), 'notes': 'Phosphor bronze impeller'}
        )
        BOMItem.objects.update_or_create(
            bom=bom3, raw_material=rms['RM-ROTOR-005'],
            defaults={'quantity_required': Decimal('1.00'), 'wastage_percentage': Decimal('0.00'), 'notes': 'Drive shaft'}
        )
        BOMItem.objects.update_or_create(
            bom=bom3, raw_material=rms['RM-BRG-004'],
            defaults={'quantity_required': Decimal('2.00'), 'wastage_percentage': Decimal('0.00'), 'notes': 'Heavy duty bearing support'}
        )

        # 5. Customers (Module 1: Order Booking)
        customers_data = [
            {
                'code': 'CUST-2026-001',
                'company_name': 'Tata Motors Heavy Commercial Plant',
                'contact_person': 'Rajendra Singh',
                'email': 'procurement.tata@tatamotors.com',
                'phone': '+91 98201 44512',
                'gst_number': '27AAACT2727Q1ZW',
                'billing_address': 'Plot No. 12, Pimpri Industrial Belt, MIDC',
                'city': 'Pune',
                'state': 'Maharashtra',
                'pincode': '411018',
            },
            {
                'code': 'CUST-2026-002',
                'company_name': 'Larsen & Toubro Heavy Engineering Div',
                'contact_person': 'Sunita Krishnan',
                'email': 's.krishnan@larsentoubro.com',
                'phone': '+91 97112 88921',
                'gst_number': '24AAACL0140P1ZT',
                'billing_address': 'L&T Manufacturing Complex, Gate 4, Hazira Works',
                'city': 'Surat',
                'state': 'Gujarat',
                'pincode': '394510',
            },
            {
                'code': 'CUST-2026-003',
                'company_name': 'Kirloskar Brothers Industrial Fluidics',
                'contact_person': 'Mahesh Joshi',
                'email': 'mjoshi@kirloskarfluidics.com',
                'phone': '+91 94220 55192',
                'gst_number': '27AAACK0821M1ZX',
                'billing_address': 'Udyog Bhavan, Tilak Road, Swargate',
                'city': 'Pune',
                'state': 'Maharashtra',
                'pincode': '411002',
            },
            {
                'code': 'CUST-2026-004',
                'company_name': 'Godrej Process Equipment Division',
                'contact_person': 'Farhan Merchant',
                'email': 'fmerchant@godrej.com',
                'phone': '+91 98330 90214',
                'gst_number': '27AAACG0542G1ZP',
                'billing_address': 'Plant 16, Pirojshanagar, Vikhroli East',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400079',
            },
        ]

        custs = {}
        for c_item in customers_data:
            c, _ = Customer.objects.update_or_create(
                code=c_item['code'],
                defaults=c_item
            )
            custs[c.code] = c

        # 6. Vendors (Module 3: Procurement & PO)
        vendors_data = [
            {
                'code': 'VND-2026-001',
                'company_name': 'Steel Authority of India Special Castings',
                'contact_person': 'Alok Ranjan',
                'email': 'sales@sailcastings.gov.in',
                'phone': '+91 91234 56780',
                'gst_number': '20AAACS1234F1Z1',
                'address': 'Industrial Area Sector 4, Bokaro Steel City',
                'city': 'Bokaro',
                'state': 'Jharkhand',
                'pincode': '827004',
                'payment_terms': 'Net 30 Days',
                'rating': Decimal('4.8'),
            },
            {
                'code': 'VND-2026-002',
                'company_name': 'Hindalco Industries Copper & Conductor Div',
                'contact_person': 'Meena Agarwal',
                'email': 'orders@hindalcowire.com',
                'phone': '+91 98765 43210',
                'gst_number': '23AAACH0001K1ZZ',
                'address': 'Dahej PCPIR Special Economic Zone',
                'city': 'Bharuch',
                'state': 'Gujarat',
                'pincode': '392130',
                'payment_terms': 'Net 15 Days',
                'rating': Decimal('4.9'),
            },
            {
                'code': 'VND-2026-003',
                'company_name': 'SKF Bearings & Industrial Motion India Ltd',
                'contact_person': 'Girish Rao',
                'email': 'grao@skfindia.com',
                'phone': '+91 99200 11223',
                'gst_number': '27AAACS0099Q1ZV',
                'address': 'Chinchwad Industrial Area, Pune-Mumbai Highway',
                'city': 'Pune',
                'state': 'Maharashtra',
                'pincode': '411033',
                'payment_terms': 'Net 45 Days',
                'rating': Decimal('5.0'),
            },
        ]

        vends = {}
        for v_item in vendors_data:
            v, _ = Vendor.objects.update_or_create(
                code=v_item['code'],
                defaults=v_item
            )
            vends[v.code] = v

        # 7. Sales Orders (Module 1: Order Booking)
        today = datetime.date.today()

        # Order 1: In Production (Tata Motors)
        so1, _ = SalesOrder.objects.update_or_create(
            order_number='SO-2026-0001',
            defaults={
                'customer': custs['CUST-2026-001'],
                'order_date': today - datetime.timedelta(days=12),
                'delivery_due_date': today + datetime.timedelta(days=8),
                'priority': 'HIGH',
                'status': 'IN_PRODUCTION',
                'payment_terms': 'Net 30 Days',
                'special_instructions': 'High ambient temperature winding (Class H insulation). Tropicalized varnish coating.',
                'created_by': created_users['sales_officer'],
            }
        )
        SalesOrderItem.objects.update_or_create(
            order=so1, product=prods['FG-MTR-5HP'],
            defaults={
                'quantity': 10,
                'unit_price': prods['FG-MTR-5HP'].selling_price,
                'discount_percentage': Decimal('5.00'),
                'specifications': 'Class H insulation, IP55, 415V 50Hz'
            }
        )
        so1.recalculate_totals()

        # Order 2: Delivered & Ready for Invoice / Invoiced (L&T)
        so2, _ = SalesOrder.objects.update_or_create(
            order_number='SO-2026-0002',
            defaults={
                'customer': custs['CUST-2026-002'],
                'order_date': today - datetime.timedelta(days=25),
                'delivery_due_date': today - datetime.timedelta(days=3),
                'priority': 'URGENT',
                'status': 'DELIVERED',
                'payment_terms': 'Net 30 Days',
                'special_instructions': 'Full third-party inspection report (TUV Rheinland) required on dispatch.',
                'created_by': created_users['sales_officer'],
            }
        )
        SalesOrderItem.objects.update_or_create(
            order=so2, product=prods['FG-GEAR-01'],
            defaults={
                'quantity': 4,
                'unit_price': prods['FG-GEAR-01'].selling_price,
                'discount_percentage': Decimal('2.50'),
                'specifications': 'Synthetic Mobil SHC 630 gear oil filled, test report attached'
            }
        )
        SalesOrderItem.objects.update_or_create(
            order=so2, product=prods['FG-MTR-5HP'],
            defaults={
                'quantity': 4,
                'unit_price': prods['FG-MTR-5HP'].selling_price,
                'discount_percentage': Decimal('0.00'),
                'specifications': 'Coupled drive package'
            }
        )
        so2.recalculate_totals()

        # Order 3: Confirmed (Kirloskar)
        so3, _ = SalesOrder.objects.update_or_create(
            order_number='SO-2026-0003',
            defaults={
                'customer': custs['CUST-2026-003'],
                'order_date': today - datetime.timedelta(days=2),
                'delivery_due_date': today + datetime.timedelta(days=15),
                'priority': 'MEDIUM',
                'status': 'CONFIRMED',
                'payment_terms': 'Net 45 Days',
                'special_instructions': 'Dynamic hydrostatic pressure test at 15 bar for 30 minutes.',
                'created_by': created_users['sales_officer'],
            }
        )
        SalesOrderItem.objects.update_or_create(
            order=so3, product=prods['FG-PUMP-10HP'],
            defaults={
                'quantity': 6,
                'unit_price': prods['FG-PUMP-10HP'].selling_price,
                'discount_percentage': Decimal('4.00'),
                'specifications': 'Phosphor bronze impeller with mechanical seal type Burgmann M7N'
            }
        )
        so3.recalculate_totals()

        # 8. Purchase Orders & Goods Receipt (Module 3: Procurement & PO)
        # PO 1: Completed and Received via GRN
        po1, _ = PurchaseOrder.objects.update_or_create(
            po_number='PO-2026-0001',
            defaults={
                'vendor': vends['VND-2026-003'],
                'linked_sales_order': so1,
                'order_date': today - datetime.timedelta(days=15),
                'expected_delivery_date': today - datetime.timedelta(days=7),
                'status': 'COMPLETED',
                'notes': 'Urgent bearing procurement for Tata Motors SO-2026-0001 line.',
                'created_by': created_users['proc_officer'],
            }
        )
        PurchaseOrderItem.objects.update_or_create(
            purchase_order=po1, raw_material=rms['RM-BRG-004'],
            defaults={
                'quantity_ordered': Decimal('50.00'),
                'quantity_received': Decimal('50.00'),
                'unit_price': rms['RM-BRG-004'].standard_cost,
                'tax_rate': Decimal('18.00'),
            }
        )
        po1.recalculate_totals()

        grn1, _ = GoodsReceiptNote.objects.update_or_create(
            grn_number='GRN-2026-0001',
            defaults={
                'purchase_order': po1,
                'receipt_date': today - datetime.timedelta(days=7),
                'challan_number': 'SKF-DC-88491',
                'remarks': '100% visual and dimensional inspection cleared. Staged in Bay F.',
                'received_by': created_users['proc_officer']
            }
        )

        # PO 2: Issued to Hindalco for Copper Wire (Shortage restock)
        po2, _ = PurchaseOrder.objects.update_or_create(
            po_number='PO-2026-0002',
            defaults={
                'vendor': vends['VND-2026-002'],
                'order_date': today - datetime.timedelta(days=4),
                'expected_delivery_date': today + datetime.timedelta(days=3),
                'status': 'ISSUED',
                'notes': 'Replenishing copper wire winding stock following BOM shortage alert.',
                'created_by': created_users['proc_officer'],
            }
        )
        PurchaseOrderItem.objects.update_or_create(
            purchase_order=po2, raw_material=rms['RM-COP-002'],
            defaults={
                'quantity_ordered': Decimal('150.00'),
                'quantity_received': Decimal('0.00'),
                'unit_price': rms['RM-COP-002'].standard_cost,
                'tax_rate': Decimal('18.00'),
            }
        )
        po2.recalculate_totals()

        # Log Vendor Communication
        VendorCommunication.objects.get_or_create(
            vendor=vends['VND-2026-002'],
            purchase_order=po2,
            subject='Dispatch tracking for Copper Wire consignment',
            defaults={
                'channel': 'PHONE',
                'message': 'Called supplier Ms. Meena Agarwal. Consignment dispatched via V-Trans lorry #MH12-RN-9921, arrival expected within 48 hours.',
                'logged_by': created_users['proc_officer']
            }
        )

        # 9. Invoices (Module 4: Invoice Generation)
        # Invoice 1: Issued to L&T (Paid)
        inv1, _ = Invoice.objects.update_or_create(
            invoice_number='INV-2026-0001',
            defaults={
                'sales_order': so2,
                'customer': custs['CUST-2026-002'],
                'invoice_date': today - datetime.timedelta(days=18),
                'due_date': today + datetime.timedelta(days=12),
                'status': 'PAID',
                'payment_terms': 'Net 30 Days',
                'subtotal': so2.subtotal,
                'cgst_rate': Decimal('9.00'),
                'cgst_amount': round(so2.subtotal * Decimal('0.09'), 2),
                'sgst_rate': Decimal('9.00'),
                'sgst_amount': round(so2.subtotal * Decimal('0.09'), 2),
                'igst_rate': Decimal('0.00'),
                'discount_amount': so2.discount_amount,
                'grand_total': so2.grand_total,
                'amount_paid': so2.grand_total,
                'amount_due': Decimal('0.00'),
                'created_by': created_users['accountant'],
            }
        )
        for item in so2.items.all():
            InvoiceItem.objects.update_or_create(
                invoice=inv1,
                product=item.product,
                defaults={
                    'description': f"{item.product.name} (P.O. Ref: LT-ENG-2026)",
                    'hsn_sac_code': '8501',
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'tax_rate': Decimal('18.00'),
                    'line_total': item.line_total
                }
            )

        # Invoice 2: Issued to Tata Motors (Partially Paid)
        inv2, _ = Invoice.objects.update_or_create(
            invoice_number='INV-2026-0002',
            defaults={
                'sales_order': so1,
                'customer': custs['CUST-2026-001'],
                'invoice_date': today - datetime.timedelta(days=5),
                'due_date': today + datetime.timedelta(days=25),
                'status': 'PARTIALLY_PAID',
                'payment_terms': 'Net 30 Days',
                'subtotal': so1.subtotal,
                'cgst_rate': Decimal('9.00'),
                'cgst_amount': round(so1.subtotal * Decimal('0.09'), 2),
                'sgst_rate': Decimal('9.00'),
                'sgst_amount': round(so1.subtotal * Decimal('0.09'), 2),
                'igst_rate': Decimal('0.00'),
                'discount_amount': so1.discount_amount,
                'grand_total': so1.grand_total,
                'amount_paid': Decimal('150000.00'),
                'amount_due': so1.grand_total - Decimal('150000.00'),
                'created_by': created_users['accountant'],
            }
        )
        for item in so1.items.all():
            InvoiceItem.objects.update_or_create(
                invoice=inv2,
                product=item.product,
                defaults={
                    'description': f"{item.product.name} (Ref: SO-2026-0001)",
                    'hsn_sac_code': '8501',
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'tax_rate': Decimal('18.00'),
                    'line_total': item.line_total
                }
            )

        # 10. Payments & Reconciliation (Module 5: Payment)
        # Payment 1: Full settlement from L&T
        Payment.objects.update_or_create(
            payment_number='PAY-2026-0001',
            defaults={
                'payment_type': 'CUSTOMER_RECEIPT',
                'invoice': inv1,
                'customer': custs['CUST-2026-002'],
                'amount': inv1.grand_total,
                'payment_date': today - datetime.timedelta(days=8),
                'payment_method': 'BANK_TRANSFER',
                'reference_number': 'NEFT-HDFC-991823019',
                'status': 'COMPLETED',
                'is_reconciled': True,
                'notes': 'Full settlement received via HDFC corporate bank transfer for INV-2026-0001.',
                'recorded_by': created_users['accountant'],
            }
        )

        # Payment 2: Advance/Part settlement from Tata Motors
        Payment.objects.update_or_create(
            payment_number='PAY-2026-0002',
            defaults={
                'payment_type': 'CUSTOMER_RECEIPT',
                'invoice': inv2,
                'customer': custs['CUST-2026-001'],
                'amount': Decimal('150000.00'),
                'payment_date': today - datetime.timedelta(days=2),
                'payment_method': 'BANK_TRANSFER',
                'reference_number': 'RTGS-SBI-882194012',
                'status': 'COMPLETED',
                'is_reconciled': True,
                'notes': 'Mobilization advance payment for 5HP Induction Motors batch.',
                'recorded_by': created_users['accountant'],
            }
        )

        # Payment 3: Outflow vendor payment to SKF Bearings
        Payment.objects.update_or_create(
            payment_number='PAY-2026-0003',
            defaults={
                'payment_type': 'VENDOR_PAYMENT',
                'purchase_order': po1,
                'vendor': vends['VND-2026-003'],
                'amount': po1.total_amount,
                'payment_date': today - datetime.timedelta(days=5),
                'payment_method': 'BANK_TRANSFER',
                'reference_number': 'NEFT-ICICI-00912491',
                'status': 'COMPLETED',
                'is_reconciled': True,
                'notes': 'Full settlement against invoice and GRN-2026-0001.',
                'recorded_by': created_users['accountant'],
            }
        )

        # 11. Realistic Audit Trail Logs (Module 7)
        logs = [
            ('LOGIN', 'USERS', 'User Vikram Malhotra logged into OrderCraft ERP', admin_user.id),
            ('CREATE', 'ORDERS', 'Booked new sales order SO-2026-0001 for Tata Motors Heavy Commercial Plant (₹282256.00)', so1.id),
            ('EXPLODE_BOM', 'BOM', 'Ran BOM explosion for 10 units of 5HP Three-Phase Induction Motor. Shortage detected in Copper Wire & Bearings.', bom1.id),
            ('CREATE', 'PROCUREMENT', 'Issued purchase order PO-2026-0001 to SKF Bearings for 50 pcs ball bearings (₹18880.00)', po1.id),
            ('RECEIVE_GOODS', 'PROCUREMENT', 'Goods received under GRN-2026-0001. Raw material RM-BRG-004 stock incremented by 50 pcs.', rms['RM-BRG-004'].id),
            ('STATUS_CHANGE', 'ORDERS', 'Changed order SO-2026-0001 status from CONFIRMED to IN_PRODUCTION', so1.id),
            ('CREATE', 'INVOICES', 'Issued tax invoice INV-2026-0001 to Larsen & Toubro Heavy Engineering (₹291932.00)', inv1.id),
            ('CREATE', 'PAYMENTS', 'Recorded customer payment receipt PAY-2026-0001 of ₹291932.00 via Bank Transfer (NEFT)', inv1.id),
            ('RECONCILE', 'PAYMENTS', 'Auto-reconciled Invoice INV-2026-0001 to status PAID', inv1.id),
        ]

        for action, module, desc, rec_id in logs:
            AuditLog.objects.get_or_create(
                action=action,
                module=module,
                description=desc,
                defaults={
                    'user': admin_user,
                    'user_name': admin_user.get_full_name(),
                    'record_id': str(rec_id),
                    'ip_address': '127.0.0.1'
                }
            )

        self.stdout.write(self.style.SUCCESS(">> Successfully seeded OrderCraft ERP with realistic manufacturing data!"))
        self.stdout.write(self.style.SUCCESS(f">> Users created: {len(created_users)} (Default password for all users: ordercraft123)"))
        self.stdout.write(self.style.SUCCESS(f">> Products: {Product.objects.count()} | BOMs: {BillOfMaterial.objects.count()} | Raw Materials: {RawMaterial.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f">> Orders: {SalesOrder.objects.count()} | POs: {PurchaseOrder.objects.count()} | Invoices: {Invoice.objects.count()} | Payments: {Payment.objects.count()}"))
