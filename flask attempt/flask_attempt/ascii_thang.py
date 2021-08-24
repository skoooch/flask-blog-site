def ascii_main(image_file):
	from PIL import Image
	luminance = "@B%8&WM#0Qvnxjf/\\|?+<>i!;:\",^.'` "
	luminance_small =  ' .:-=+*#%@'
	with Image.open(image_file) as im:
		im = im.convert("L")
	width, height = im.size
	f = open('TextFile.txt','w')

	ope = im.resize((round(width/10),round(height/10)))
	counter = 0
	for y in list(ope.getdata()):
		if counter >= (round(width/10)):
			f.write('\n')
			counter = 0
		index = round(y *0.1294117647)

		f.write(luminance[index-1])
		f.write(luminance[index-1])
		f.write(luminance[index-1])
		counter += 1




		