export type ServiceMatch={id:string;label:string;detail?:string;draft?:string;source?:{label:string;url:string}};
export type GuideResult={state:"match"|"clarify"|"none";method:"model2vec"|"keywords";categories:{id:string;name:string}[];resourceIds:string[];matches:ServiceMatch[]};
