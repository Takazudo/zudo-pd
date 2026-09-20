"""Authoritative compact Board B mechanical and placement dimensions, in mm."""
WIDTH, HEIGHT = 110, 85
P1_CENTER = (40, 1.8)
MOUNTING_HOLES = [(4,23),(4,4),(32.6,14.2),(106,4),(4,81),(106,81)]
FIDUCIALS = [(9.5,6),(107,27),(18,80)]
PLACEMENTS = {
 'J5':(37.7,14.1,90,'bottom'),'P1':(*P1_CENTER,0),
 'J6':(7,36,90),'J7':(7,49,90),
 'J10':(41.4,HEIGHT-12.23,0),'J11':(81.5,HEIGHT-12.23,0),
 'U2':(29,18,180),'L1':(37,18,0),'R1':(26,12,90),'R2':(23,15,0),
 'C5':(12,19,90),'C6':(29,21,0),'C39':(29,24.5,0),'C46':(21.5,29,180),
 'C38':(30,13.5,90),'C3':(45,18,0),'C14':(45,13.5,0),'C20':(45,22.5,0),
 'C36':(51,16,0),'C37':(51,20.5,0),
 'U3':(23,46,0),'D2':(35,45,90),'L2':(47,44,0),'C7':(24,58,180),
 'C8':(34,51,0),'C4':(62,44,0),'C32':(39,34,0),'R3':(34,37,0),'R4':(29,36,90),
 'C15':(63,36,90),'C22':(63,53,90),
 'U4':(23,70,0),'D3':(35,71,90),'L3':(47,70,0),'C9':(21.7,83,180),
 'C10':(34,77,0),'C11':(62,65,0),'C33':(38.3,59,0),'R5':(34,63,0),'R6':(32,60,90),
 'C16':(57,57.5,90),'C24':(61.5,77.8,90),'C12':(48,57,0),
 'U6':(77,16,0),'U7':(77,44,0),'U8':(77,70,0),
 'C17':(86,24,0),'C40':(89,16,0),'C21':(100,29,0),'PTC1':(102,11,90),'TVS1':(106,19,90),
 'C18':(86,52,0),'C41':(89,44,0),'C23':(100,55,0),'PTC2':(102,39,90),'TVS2':(106,47,90),
 'C19':(86,62,0),'C42':(89,70,180),'C25':(102.9,78.8,180),'PTC3':(102,65,90),'TVS3':(106,69.7,90),
 'R20':(90,6,0),'R21':(90,9,0),'R22':(96,9,0),
 'R23':(90,34,0),'R24':(90,37,0),'R25':(96,37,0),
 'TP3':(63,9,0),'TP4':(63,31,0),'TP5':(66,59,0),
 'LED2':(63,86.5,90),'LED3':(63,89.9,90),'LED4':(63,93.3,90),
 'R7':(58,86.5,0),'R8':(58,89.9,0),'R9':(58,93.3,0),
}
# Placement transformations from the reviewed 110x95 layout.
BUCK_REFS = {'U2','L1','R1','R2','C6','C39','C38','C3','C14','C20','C36','C37'}
TOP_LDO_REFS = {'U6','C40','C17','C21','PTC1','TVS1','R20','R21','R22'}
FIXED_REFS = BUCK_REFS | TOP_LDO_REFS | {'J5','P1','J6','J7','J10','J11','C5','C46','TP3','TP4','TP5'}
for ref,pos in list(PLACEMENTS.items()):
    if ref in BUCK_REFS:PLACEMENTS[ref]=(pos[0]+14,pos[1]-3,*pos[2:])
    elif ref in TOP_LDO_REFS:PLACEMENTS[ref]=(pos[0]-3,pos[1],*pos[2:])
    elif ref not in FIXED_REFS:PLACEMENTS[ref]=(pos[0],pos[1]-10,*pos[2:])
PLACEMENTS.update({'C5':(14,19,90),'C46':(16,7.5,180),'R2':(40.5,11.75,0),
                   'C21':(99,18,90),'PTC1':(100.5,6.5,90),'TVS1':(108,17.5,90),
                   'R22':(92,9,0),'C32':(38,25,0),
                   'C3':(57.7,9,90),'C14':(57.7,15.5,90),'C20':(57.7,22,90),
                   'C36':(62.3,9,90),'C37':(62.3,15.5,90),'TP3':(46.35,1.8,0),'TP4':(48.89,1.8,0),'TP5':(51.43,1.8,0)})

def route_offset(ref):
    if ref in BUCK_REFS:return (14,-3)
    if ref in TOP_LDO_REFS:return (-3,0)
    return (0,-10)

def pd_to_board_b(point):
    # Rotate the reusable module in-plane; USB remains at the outside left edge.
    x,y=point
    return (y,27-x)

# Negative islands and the sampled return corridor move with the lower rows.
NEGATIVE_ZONES = {
 'U4': {'F.Cu':[(7,52),(30,52),(30,79),(7,79)],
        'B.Cu':[(7,52),(30,52),(30,84),(7,84)]},
 'U8': {'F.Cu':[(63,49),(80,49),(80,84),(63,84)],
        'B.Cu':[(66,49),(109,49),(109,84),(66,84)]},
}
GROUND_CORRIDOR = {'x_start':31, 'x_end':65, 'ys':[54,60,67], 'minimum_aggregate_mm':20,'minimum_largest_mm':10}


def edge_primitives():
    return [{'type':'line','start':a,'end':b} for a,b in
            [([0,0],[WIDTH,0]),([WIDTH,0],[WIDTH,HEIGHT]),
             ([WIDTH,HEIGHT],[0,HEIGHT]),([0,HEIGHT],[0,0])]]


GROUND_STITCHES = [(40,54),(48,56),(58,60),(50,64),(48,62),(52,64),(54,64)]
