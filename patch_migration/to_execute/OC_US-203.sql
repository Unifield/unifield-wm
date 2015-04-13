# To be executed in instances typed OC
update ir_model_data set last_modification=now() , touched='[''name'']' where model='financing.contract.donor';
update ir_model_data set last_modification=now() , touched='[''name'']' where model='financing.contract.format.line';
update ir_model_data set last_modification=now() , touched='[''format_name'']' where model='financing.contract.format';
