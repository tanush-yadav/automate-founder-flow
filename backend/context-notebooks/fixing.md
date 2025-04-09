Inconsistent Parameter Handling

- use_mocks is inconsistently passed through tasks (sometimes missing)
  Remove this entirely but mindfully as we don't use it anyways. We don't mock requests. Fill the gaps here as where and where exactly should we remove it. \_\_\_ agent will fill this as a plan

- The limit parameter was added but inconsistently applied across endpoints
  We need to correctly implement this, as limit is required when we prepare the query and should be mindfully used wherever required. Fill the gaps here, as to where we might need this fixing. \_\_\_ agent will fill this as a plan

Fragmented Error Handling

- Some places use detailed traceback printing, others just error messages
  We should always use detailed traceback so we know what might be wrong.

- Status values are inconsistent ("Failed", "ReadyToSend", "Pending", "Scheduled")
