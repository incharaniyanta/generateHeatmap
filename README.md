# generateHeatmap
Heatmap for logo detection

## Code Overview
Annotations for Visa during the 2018 World Cup Final. 

## Input:
labels.txt – the provided file contains references to images and associated annotations.  The file is of the format of one image per line as follows:

image_path number_of_annotations x1 y1 x2 y2 x3 y3 x4 y4 …. (repeat the coordinates for number_of_annotations on this line)

In our case, the labels.txt references frames in the visa_frames directory along annotations of Visa for each frame.  These are all of the frames where Visa occurred during the 2018 World Cup Final, sampled at one frame per second.

Note: The reason we specify 4 (x,y) coordinates instead of x,y,width,height is for added flexibility, as we output quadrilaterals in our logo detection solution.

## Output:
highlighted frames – For each frame specified in labels.txt, we highlight the associated annotations on the image and save the drawn image to “output” directory. 

heatmap – At the end of the script a heatmap is saved to the working directory as “heatmap.png”.  
