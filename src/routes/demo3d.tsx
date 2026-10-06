import { createFileRoute } from "@tanstack/react-router";
import { ModelPanel } from "@/components/bim/ModelPanel";
import { buildingModelSchema } from "@/lib/bim/schema";
const m = buildingModelSchema.parse({levels:[{id:"rdc",name:"RDC",elevation:0,height:2.8},{id:"r1",name:"R+1",elevation:2.8,height:2.8}],
rooms:[{id:"p1",name:"Séjour",levelId:"rdc",polygon:[[0,0],[6,0],[6,5],[0,5]]},{id:"p2",name:"Cuisine",levelId:"rdc",polygon:[[6,0],[10,0],[10,5],[6,5]]},{id:"p3",name:"Chambre",levelId:"r1",polygon:[[0,0],[10,0],[10,5],[0,5]]}],
walls:["rdc","r1"].flatMap(l=>[{id:l+"a",levelId:l,start:[0,0],end:[10,0],type:"exterieur"},{id:l+"b",levelId:l,start:[10,0],end:[10,5],type:"exterieur"},{id:l+"c",levelId:l,start:[10,5],end:[0,5],type:"exterieur"},{id:l+"d",levelId:l,start:[0,5],end:[0,0],type:"exterieur"}]).concat([{id:"mi",levelId:"rdc",start:[6,0],end:[6,5]} as never]),
openings:[{id:"o1",wallId:"rdca",kind:"porte",offset:2,width:1,height:2.1},{id:"o2",wallId:"rdca",kind:"fenetre",offset:7,width:1.5,height:1.2,sill:1},{id:"o3",wallId:"r1a",kind:"fenetre",offset:4,width:2,height:1.2,sill:1}],
roof:{type:"quatre_pans"}});
export const Route = createFileRoute("/demo3d")({ component: () => <div className="p-6"><ModelPanel projectId="demo" model={m} /></div> });
