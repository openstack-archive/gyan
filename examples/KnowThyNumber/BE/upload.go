package main

import (
	"bytes"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"io"
	"io/ioutil"
	"math"
	"mime/multipart"
	"net/http"
	"os"

	"github.com/disintegration/imaging"
	"github.com/harrydb/go/img/grayscale"
	// "github.com/nfnt/resize"
)

// UploadFile uploads a file to the server
func UploadFile(w http.ResponseWriter, r *http.Request) {
	fmt.Printf("Inside upload \n")
	if r.Method != http.MethodPost {
		http.Redirect(w, r, "/", http.StatusSeeOther)
		return
	}

	// Save a copy of this request for debugging.
	//requestDump, err := httputil.DumpRequest(r, true)
	//if err != nil {
	//	fmt.Println(err)
	//}

	//fmt.Println(string(requestDump))

	file, handle, err := r.FormFile("file")
	if err != nil {
		fmt.Printf("upload error\n")
		fmt.Println(err.Error())
		fmt.Fprintf(w, "%v", err)
		return
	}
	defer file.Close()

	mimeType := handle.Header.Get("Content-Type")
	switch mimeType {
	// case "image/jpeg":
	//	saveFile(w, file, handle)
	case "image/png":
		saveFile(w, file, handle)
	default:
		jsonResponse(w, http.StatusBadRequest, "The format file is not valid.")
	}
}

func processImage(infile multipart.File) (err error) {
	imgSrc, _, err := image.Decode(infile)
	if err != nil {
		panic(err.Error())
	}

	// Create a new grayscale image
	bounds := imgSrc.Bounds()
	w, h := bounds.Max.X, bounds.Max.Y
	grayScale := image.NewGray(image.Rectangle{image.Point{0, 0}, image.Point{w, h}})
	for x := 0; x < w; x++ {
		for y := 0; y < h; y++ {
			imageColor := imgSrc.At(x, y)
			rr, gg, bb, _ := imageColor.RGBA()
			r := math.Pow(float64(rr), 2.2)
			g := math.Pow(float64(gg), 2.2)
			b := math.Pow(float64(bb), 2.2)
			m := math.Pow(0.2125*r+0.7154*g+0.0721*b, 1/2.2)
			Y := uint16(m + 0.5)
			grayColor := color.Gray{uint8(Y >> 8)}
			grayScale.Set(x, y, grayColor)
		}
	}

	//Resize image
	newImg := imaging.Resize(imgSrc, 28, 28, imaging.Lanczos)

	// Grayscale 2
	grayImg := grayscale.Convert(newImg, grayscale.ToGrayLuminance)
	threshold := grayscale.Otsu(grayImg)
	grayscale.Threshold(grayImg, threshold, 0, 255)

	// Encode the grayscale image to the new file
	newFileName := "grayscale.png"
	newfile, err := os.Create("./files/" + newFileName)
	if err != nil {
		fmt.Printf("failed creating %s: %s", newfile, err)
		return err
	}
	//defer newfile.Close()
	//png.Encode(newfile, grayScale)
	png.Encode(newfile, grayImg)

	return nil
}

func saveFile(w http.ResponseWriter, file multipart.File, handle *multipart.FileHeader) {
	err := processImage(file)
	//data, err := ioutil.ReadAll(file2)
	if err != nil {
		fmt.Fprintf(w, "%v", err)
		fmt.Println("%v", err)
		return
	}

	//err = ioutil.WriteFile("./files/"+handle.Filename, data, 0666)
	//if err != nil {
	//	fmt.Fprintf(w, "%v", err)
	//	return
	//}
	resp := predictNumber()
	jsonResponse(w, http.StatusCreated, resp)
}

func postFile(filename string, targetUrl string) (string, error) {
	bodyBuf := &bytes.Buffer{}
	bodyWriter := multipart.NewWriter(bodyBuf)

	// this step is very important
	fileWriter, err := bodyWriter.CreateFormFile("file", filename)
	if err != nil {
		fmt.Println("error writing to buffer")
		return "", err
	}

	// open file handle
	fh, err := os.Open(filename)
	if err != nil {
		fmt.Println("error opening file")
		return "", err
	}
	defer fh.Close()

	//iocopy
	_, err = io.Copy(fileWriter, fh)
	if err != nil {
		return "", err
	}

	contentType := bodyWriter.FormDataContentType()
	bodyWriter.Close()

	resp, err := http.Post(targetUrl, contentType, bodyBuf)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	resp_body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	fmt.Println(resp.Status)
	fmt.Println(string(resp_body))
	return string(resp_body), nil
}

func predictNumber() string {
	target_url := "http://localhost:5000/mnist/classify"
	filename := "./files/grayscale.png"
	resp, _ := postFile(filename, target_url)
	return resp
}

func jsonResponse(w http.ResponseWriter, code int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	fmt.Fprint(w, message)
}
