--    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--                            Trabacus - Invoice Report
--    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    select ai.id, 
    	rp.name as customer_name,
    	rp.ref as customer_id,
    	rp.street as customer_street,
    	rp.street2 as customer_street2,
    	(select name from tr_city where id = rp.city_id) as customer_city,
    	(select name from res_country_state where id = rp.state_id) as customer_state,
    	(select name from res_country where id = rp.country_id) as customer_country,
    	rp.zip as customer_zip,
    	rp.mobile as customer_mobile,
    	rp.phone as customer_phone,
    	rp.email as customer_email,
    	ai.number as invoice_no,
    	(select lead_no from crm_lead where id = ai.lead_id) as lead_no,
    	ai.date_invoice as invoice_date,
    	ai.type as inv_type,ail.id as line_id,
    	ai.travel_type as travel_type,
    	ail.basic as basic,
    	ail.other as other,
    	(case when ail.basic is null then 0 else ail.basic end)
    		+(case when ail.other is null then 0 else ail.other end) as ln_sub_total,
    	ail.servicechrg as servicecharge,
    	ail.disount as discount,
    	ail.cancel_markup as cancel_markup,
    	ail.cancel_charges as cancel_charges,
    	ail.cancel_service as cancel_service,
    	ai.amount_total as total,
    	ail.passenger as passenger,
    	
    	case when ail.flight_id is not null then ail.flight_id else null end as flight_id,
    	case when ail.hotel_id is not null then ail.hotel_id else null end as hotel_id,
    	case when ail.visa_id is not null then ail.visa_id else null end as visa_id,
    	case when ail.rail_id is not null then ail.rail_id else null end as rail_id,
    	case when ail.car_id is not null then ail.car_id else null end as car_id,
    	case when ail.ins_id is not null then ail.ins_id else null end as ins_id,
    	case when ail.cruise_id is not null then ail.cruise_id else null end as cruise_id,
    	case when ail.activity_id is not null then ail.activity_id else null end as activity_id,
    	case when ail.addon_id is not null then ail.addon_id else null end as addon_id,
    	
    	(case when ail.hotel_id is not null then (select adult_type from tr_invoice_hotel where id = ail.hotel_id) end ) as adult_type,
     	(select rp.name from res_users re,res_partner rp where re.partner_id = rp.id and re.id = ai.user_id)as booked_by,
    	(select cr.name from res_currency cr where cr.id = ai.currency_id) as Currency_Name,
    	(select count(id) from account_invoice_tax where invoice_id = ai.id) as tax_count
    	
    from account_invoice ai 
    inner join account_invoice_line ail on ail.invoice_id = ai.id
    inner join res_partner rp on  rp.id = ai.partner_id 
    where ai.id in (${ids}) and ai.state in ('open','paid')

--    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--                            Trabacus - Invoice SubReports
--    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

--    1. Flight Invoice Subreport

    select  
    	  (select code from tr_airport where id = fl.from_id) as from_code
       	, (select code from tr_airport where id = fl.to_id) as To_code
    	, fl.ft_num as Flight_no
    	, fl.dep as Departure
    	, f.inv_type as invoicetype
    	, f.ft_traveltype as servicetype
    	, f.ticket_no as Ticket_no
    
    from tr_invoice_flight f
    left outer join tr_invoice_flight_lines fl on fl.flight_id = f.id
    where f.id in (${flight_id}) order by fl.id



--    2. Hotel Invoice Subreport
--    3. Visa Invoice Subreport
--    4. Insurance Invoice Subreport

--    5. Cruise Invoice Subreport
--    6. Railway Invoice Subreport
--    7. Addons Invoice Subreport
--    8. Activity Invoice Subreport



--    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--                            Daily Payment Receipts Reports
--    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


drop type if exists dt_tr_payment_receipt cascade;
 
create type dt_tr_payment_receipt as (
	voucher_id int
	, payment_date date
	, pay_number varchar(64)
	, payment_method varchar(64)
	, payment_type varchar(64)
	, cheque_no varchar(30)
	, cheque_date date
	, bank_name varchar(64)
	, bank_branch varchar(64)
	, client_code varchar(64)
	, client_name varchar(60)
	, currency_name varchar(60)
	, currency_symbol varchar(60)
	, company_currency varchar(60)
	, journal_currency varchar(60)
	, amount_foreign float
	, rate_of_exchange float
	, amount_local float
	, payment_reference varchar(1000)
	, voucher_name_memo varchar(64)
	, voucher_type varchar(64)
	, company_id int
	, company_name varchar(64)
	, company_street varchar(128)
	, company_street2 varchar(128)
	, company_city varchar(24)
	, company_state varchar(60)
	, company_country varchar(60)
	, company_zip varchar(24)
	, company_mobile varchar(60)
	, company_phone varchar(60)
	, company_email varchar(60)
	, company_fax varchar(64)
	, company_website varchar(64)
	, company_tax_no varchar(32)
	, deposit_in varchar(64)
	, deposit_dt date
);

CREATE OR REPLACE FUNCTION func_tr_payment_receipt(start_dt date, end_dt date, vouchertype character varying, partnerid integer, groupid integer, countryid integer)
  RETURNS SETOF dt_tr_payment_receipt AS
$BODY$
DECLARE
   r dt_tr_payment_receipt%rowtype; 
   sql_str varchar(100) := '';
   str text; 
   
BEGIN     

    IF companyid > 0 THEN
	sql_str :=  sql_str || ' and v.partner_id IN (SELECT id FROM res_partner WHERE company_id = ' || companyid || ')'; 
    END iF;  
    
    IF groupid > 0 THEN
	sql_str :=  sql_str || ' and v.partner_id IN (SELECT id FROM res_partner WHERE group_id = ' || groupid || ')'; 
    END iF;     
    
    IF partnerid > 0 THEN
	sql_str :=  sql_str || ' and v.partner_id = ' || partnerid; 
    END iF;     

    str := 'select v.id as voucher_id
		, v.date as payment_date
		, v.number as pay_number
		, j.name as payment_method
		, v.pay_type as payment_type
		, v.cheque_no as cheque_no
		, v.cheque_date as cheque_date
		, (select name from res_bank where id = v.bank_id) as bank_name
		, v.branch as bank_branch
		, p.ref as client_code
		, (select name from res_partner where id = v.partner_id) as client_name
		, (case when j.currency is null then 
			(select name from res_currency where id  = c.currency_id)
			else
			(select name from res_currency where id = j.currency) end ) as currency_name
		, rcy.symbol as currency_symbol
		, (select name from res_currency where id = c.currency_id)
		, (select name from res_currency where id = j.currency)
		, v.amount as amount_foriegn
		, (select rate from res_currency_rate rcr where rcr.currency_id = rcy.id and rcr.name <= v.date order by name desc limit 1) as rate_of_exchange
		, v.amount as amount_local
		, v.reference as payment_reference
		, v.name as voucher_name_memo
		, v.type as voucher_type
		, c.id as company_id
		, c.display_compname as company_name
		, p.street as company_street
		, p.street2 as company_street2
		, (select name from tr_city where id = p.city_id) as company_city
		, (select name from res_country_state where id = p.state_id) as company_state
		, (select name from res_country where id = p.country_id) as company_country
		, p.zip as company_zip
		, p.mobile as company_mobile
		, p.phone as company_phone
		, p.email as company_email
		, p.fax as company_fax
		, p.website as company_website
		, p.tax_no as company_tax_no
		, v.deposit_in as deposit_in
		, v.deposit_dt as deposit_dt
		, v.payment_rate_currency_id
		, rcy.id
	    from account_voucher v
	    inner join account_journal j on j.id  = v.journal_id
	    inner join res_company c on c.id = v.company_id
	    inner join res_partner p on p.id = c.partner_id
	    inner join res_currency rcy on rcy.id  = v.payment_rate_currency_id
	    where v.date::date between''' || start_dt || ''' and ''' || end_dt || ''' and 
	    v.type = ''' ||vouchertype || ''' ' || sql_str;

     
    for r in execute str loop
	return next r;          
    end loop;
    
    return ;  
END 

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- 				TABLE: Outstanding 
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

drop TABLE if exists table_outstanding cascade;
CREATE TABLE table_outstanding
( id int,    
  userid int,
  moveln_id int,
  partner_id int,
  inv_date date, 
  amttype varchar(10),
  amt_original numeric,
  amt_reconciled numeric,
  tot_debit numeric,
  tot_credit numeric,
  narration text
);	
