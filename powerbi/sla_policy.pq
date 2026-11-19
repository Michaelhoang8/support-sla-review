let
 Source=Csv.Document(Binary.FromText("cHJpb3JpdHkscmVzcG9uc2Vfc2xhX2hvdXJzLHJlc29sdXRpb25fc2xhX2hvdXJzCkhpZ2gsNCwyNApOb3JtYWwsOCw3MgpMb3csMjQsMTY4Cg==",BinaryEncoding.Base64),[Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]),
 Headers=Table.PromoteHeaders(Source,[PromoteAllScalars=true]),
 Nulls=Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,Table.ColumnNames(Headers)),
 Typed=Table.TransformColumnTypes(Nulls,{{"priority",type text},{"response_sla_hours",Int64.Type},{"resolution_sla_hours",Int64.Type}},"en-US")
in Typed