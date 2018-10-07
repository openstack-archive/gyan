package main

import (
	"net/http"
)

func ping(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("pong"))
}
func main() {
	http.Handle("/", http.FileServer(http.Dir("../FE")))
	http.HandleFunc("/ping", ping)
	http.HandleFunc("/upload/", UploadFile)
	if err := http.ListenAndServe(":9000", nil); err != nil {
		panic(err)
	}
}
