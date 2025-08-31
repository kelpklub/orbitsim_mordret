import pygame
pygame.init()
screen = pygame.display.set_mode((0,0) ,pygame.FULLSCREEN)#this works 
clock =pygame.time.Clock()
swidth, sheight = screen.get_size()
font=pygame.font.SysFont(None,30)

pygame.display.set_caption("Orbit Simulation")
print (f"Screen size: {swidth}x{sheight}")#for debugimg
running = True
def up():#updates the screen wheneveranything has done drawing
    pygame.display.flip()  # Update the display
while running:
    screen.fill((0,0,0))  # Clear the screen with black

    dt =clock.tick(60)
    for event in pygame.event.get():
        mx,my = pygame.mouse.get_pos()#pos of mouse in (x,y)    
        posx,posy=mx,my
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            print(pygame.key.name(event.key),"=",event.key)#debug

            if event.key == 27:#27 is the int value for the escape key
                running = False
                
            if event.key == 9:#9 is the int value for the tab key
                print(f"Mouse position: {mx}, {my}")  # Print mouse position for debugging
                
        if pygame.mouse.get_pressed()==(True,False,False) : 
            print("mouse pressed")
            if mx>680:      
                if mx<790:
                    if my>386 :
                        if my<484 :
                            running = False
    fps =int(clock.get_fps())
    fpstxt = font.render(f"Fps :{fps}",True,(255,255,255))
    screen.blit(fpstxt,(20,10)   )        
            
    
    pygame.draw.rect(screen,(255, 0, 0), (mx,my, 100 ,100))  # Draw a red rectangle
    up()
    
    
             
                
   