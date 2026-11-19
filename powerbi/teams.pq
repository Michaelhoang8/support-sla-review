let
 Source=Csv.Document(Binary.FromText("dGVhbV9pZCx0ZWFtLHNwZWNpYWx0eQoxLEdlbmVyYWwsQWNjb3VudCBhbmQgYmlsbGluZwoyLFRlY2huaWNhbCxQcm9kdWN0IGZhdWx0cwozLFByaW9yaXR5LEVzY2FsYXRpb25zCg==",BinaryEncoding.Base64),[Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]),
 Headers=Table.PromoteHeaders(Source,[PromoteAllScalars=true]),
 Nulls=Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,Table.ColumnNames(Headers)),
 Typed=Table.TransformColumnTypes(Nulls,{{"team_id",Int64.Type},{"team",type text},{"specialty",type text}},"en-US")
in Typed