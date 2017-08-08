-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
--                                                Enquiry Details
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
drop type if exists enq_dtls cascade; 
create type enq_dtls as (id int, 
			 date_created date,
			 lead_no varchar(20),
			 date_booking varchar(15),
			 time_booking varchar(15),
			 no_covers integer,
			 stage varchar(50),
			 venue varchar(125),
			 client_name varchar(125),
			 service_type varchar(50),
			 enq_count integer); 

CREATE OR REPLACE FUNCTION enquiry_detail(date_filter character varying ,start_dt character varying, end_dt character varying, service_type character varying, customer_id integer, customer character varying, venue_id integer, stage_id integer,orderby character varying,venue_filter character varying,venue_inv_id integer,passen_type character varying)
  RETURNS SETOF enq_dtls AS
$BODY$
DECLARE
   r enq_dtls%rowtype;  
   rec record;
   st_date timestamp;
   ed_date timestamp;
   sql_str text := '';
   sort_str1 character varying(100) := '';
   sort_str2 character varying(100) := '';
   str text := ''; 

BEGIN
    
    DROP SEQUENCE if exists enq_seq;
    CREATE TEMP sequence enq_seq;
    
    DROP TABLE if exists tmp_enq;
    CREATE TEMP TABLE tmp_enq    
	( 		 id integer,
			 date_created date,
			 lead_no varchar(20),
			 date_booking varchar(15),
			 time_booking varchar(15),
			 no_covers integer,
			 stage varchar(50),
			 venue varchar(125),
			 client_name varchar(125),
			 service_type varchar(50),
			 enq_count integer)
			 
     ON COMMIT DROP;     

   if date_filter in ('date_created', 'date_booking') then
	st_date := to_char((start_dt || ' 00:00:00')::timestamp, 'yyyy-mm-dd hh24:mi:ss');
	ed_date := to_char((end_dt   || ' 23:59:59')::timestamp, 'yyyy-mm-dd hh24:mi:ss');
   end if; 

    	
    if date_filter = 'date_created' 
        then	
        str := str || 'AND cl.create_date :: timestamp between '''|| st_date ||''' and '''|| ed_date || '''';  
    elsif date_filter = 'date_booking' then      
       str := str ||' AND cl.date_requested :: timestamp between '''|| st_date ||''' and '''|| ed_date ||'''';
    end if;

    if service_type = 'venue' then
       str := str || ' AND cl.service_type = '''|| service_type || '''';

       if customer_id > 0 then
	 str := str || ' AND (cl.partner_id = ' || customer_id ||'or cl.parent_id = ' || customer_id || ')';
       end if;
    
    elsif service_type = 'noontea' then
	str := str || ' AND cl.service_type = '''|| service_type || '''';
	
	if length(customer) > 0 then
	 str := str || ' AND cl.partner_name = '''|| customer ||'''';
       end if;
        
    end if;
 
    if venue_filter = 'restaurant' then
     
       if venue_id > 0 then
          str := str || ' AND si.restaurant_id = ' || venue_id;
       end if;
    elsif venue_filter = 'group' then
        if venue_inv_id > 0 then
            str := str || ' AND si.inv_address_id = ' || venue_inv_id;
        end if;
    end if;
    
    if stage_id > 0 then
       str :=  str || ' AND cl.stage_id = ' || stage_id;
    end if; 

    if length(passen_type) > 0 then
	str :=  str || ' AND cl.passen_type = ''' || passen_type ||'''';
    end if; 

    --if length(s2) > 1 then 
     --  select 'where '|| substr(s2,5,length(s2)) into s1;
    --end if; 
  
    sql_str := 'INSERT INTO tmp_enq(id,date_created,lead_no,date_booking,time_booking,no_covers,stage,venue,client_name,service_type)
	    (SELECT nextval(''enq_seq'') as id,
		    cl.create_date,
		    cl.lead_no,
		    cl.conv_dob,
		    cl.conv_tob,
		    cl.covers,
		    (select name from crm_case_stage where id = cl.stage_id) as stage_name,
		    (select pp.name from res_partner rp inner join res_partner pp on pp.id = rp.parent_id where rp.id = si.restaurant_id) as venue,
		    (case when cl.service_type = ''venue'' then (select display_name from res_partner where id = cl.partner_id )else partner_name end) as customer_name,
		    cl.service_type       
	       from crm_lead cl,cc_send_rest_info si where cl.id = si.lead_id '|| str ||'
	       order by cl.service_type desc, '|| orderby ||'
		)';

    execute sql_str;  
  
    update tmp_enq set enq_count = (select count(id) from tmp_enq);
    
    for r in SELECT * FROM tmp_enq loop
	return next r;          
    end loop;
    
    return;  
END 

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
  

