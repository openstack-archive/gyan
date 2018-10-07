var mousePressed = false;
var lastX, lastY;
var ctx, ctx2;

function InitThis() {
    ctx = document.getElementById('myCanvas').getContext("2d");
    ctx2 = document.getElementById('myCanvas2').getContext("2d");

    $('#myCanvas').mousedown(function (e) {
        mousePressed = true;
        Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, false);
    });

    $('#clear-area').mousedown(function (e) {
        clearArea();
    });

    $('#upload-area').mousedown(function (e) {
        //uploadArea2();
    });

    $('#myCanvas').mousemove(function (e) {
        if (mousePressed) {
            Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, true);
        }
    });

    $('#myCanvas').mouseup(function (e) {
        mousePressed = false;
        //alert("mouseup")
    });

    $('#myCanvas').mouseleave(function (e) {
        mousePressed = false;
        //alert("mouseleave")
    });

    document.addEventListener('touchstart',function(e){ mapTouchEvents(e,'mousedown'); },true);
    document.addEventListener('touchmove',function(e){ mapTouchEvents(e,'mousemove'); },true);
    document.addEventListener('touchend',function(e){ mapTouchEvents(e,'mouseup'); },true);
    document.addEventListener('touchcancel',function(e){ mapTouchEvents(e,'mouseup'); },true);

}

function uploadArea() {
    alert('Inside Upload....');
    console.log("Inside Upload....");
    var image = document.getElementById("myCanvas").toDataURL("image/png").replace("image/png", "image/octet-stream");
    var data = new FormData();
    data["file"] = image;
    console.log(data);
    $.ajax({
        url: 'http://localhost:9000/upload/',
        type: 'POST',
        data: data,
        cache: false,
        dataType: 'json',
        processData: false, 
        contentType: false,  
        success: function( data , textStatus , jqXHR )
        {                
            if( typeof data.error === 'undefined' ) {                    
                submitForm( event, data ); 
            } else {                    
                alert( 'ERRORS: ' + data.error ); 
            }
        },
        error: function(jqXHR, textStatus, errorThrown) { alert( 'error on upload' ); }
        
    });
}

function getDstImage(data) {
    console.log("Entering into getDstImage")
    var fname = "./img/"
    switch(data["classification"]) {
        case 1:
            return fname+"1.jpg"
        case 2:
            return fname+"2.png"
        case 3:
            return fname+"3.png"
        case 4:
            return fname+"4.jpg"
        case 5:
            return fname+"5.png"
        case 6:
            return fname+"6.jpg"
        case 7:
            return fname+"7.png"
        case 8:
            return fname+"8.png"
        case 9:
            return fname+"9.png"
        default:
            return "error"
    }
}

function uploadArea2() {
    var canvas = document.getElementById("myCanvas")
    canvas.toBlob(
        function (blob) {
            // Do something with the blob object,
            // e.g. creating a multipart form for file uploads:
            var formData = new FormData();
            formData.append('file', blob, "predict.png");
            $.ajax({
                url: 'http://localhost:9000/upload/',
                type: 'POST',
                data: formData,
                cache: false,
                dataType: 'json',
                processData: false, 
                contentType: false,  
                success: function( data , textStatus , jqXHR )
                {                
                    if( typeof data.error === 'undefined' ) {                    
                        //submitForm( event, data ); 
                    } else {                    
                        alert( 'ERRORS: ' + data.error ); 
                    }

                    console.log("Inside success of uploadArea2")

                    var canvas = document.getElementById("myCanvas2");
                    var ctx = canvas.getContext("2d");
                    var image = new Image();
                    image.src = getDstImage(data);
                    image.onload = function() {
                        ctx.drawImage(image, 0, 0);
                    };
                },
                error: function(jqXHR, textStatus, errorThrown) { alert( 'error on upload2' ); alert(textStatus);}
                
            });
            /* ... */
        },
        'image/png'
    );

}

function Draw(x, y, isDown) {
    if (isDown) {
        ctx.beginPath();
        ctx.strokeStyle = $('#selColor').val();
        // ctx.lineWidth = $('#selWidth').val();
        ctx.lineWidth = 9;
        ctx.lineJoin = "round";
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(x, y);
        ctx.closePath();
        ctx.stroke();
    }
    lastX = x;
    lastY = y;

    //alert("Drawing done....");
    //console.log("Drawing done.....");
    //doUpload();
} 

function clearArea() {
    // Use the identity matrix while clearing the canvas
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    ctx2.setTransform(1, 0, 0, 1, 0, 0);
    ctx2.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
}