
//INIT 
$(".gram").transition({
  "opacity": 100
});


//Add truncate helper to Handlebars
Handlebars.registerHelper('truncate', function(str, len) {
  if (str && str.length > len && str.length > 0) {
    var new_str = str + " ";
    new_str = str.substr(0, len);
    new_str = str.substr(0, new_str.lastIndexOf(" "));
    new_str = (new_str.length > 0) ? new_str : str.substr(0, len);

    return new Handlebars.SafeString(new_str + '...');
  }
  return str;
});

//Create the button template
var buttonTemplate = Handlebars.compile($("#button-template").html());

//On enter in the tag entry form send the tag to be added as a subscription
$("#tag").on('keyup', function(e) {
  if (e.which == 13) {
    e.preventDefault();

    //Get the tag name
    var tag_name = $("#tag").val();

    //Send a post request and upon success add the tag to the list 
    $.post(
      "/filter", {
        "filter": tag_name
      },
      function(data, textStatus, jqXHR) {
        console.log(textStatus);

        var hashtag_list = $("#hashtag_list");

        //Create new li in the list of current filters
        hashtag_list.append(buttonTemplate({"name": tag_name}));
      });

    //Clear the input bar
    $("#tag").val("");

  }
});

//Function to be called when removing a tag
var removeTag = function(e) {


  tag = $.trim(e.currentTarget.innerText);

  $.ajax({
    url: '/filter/' + tag,
    type: 'DELETE',
    success: function(result) {
      $(e.currentTarget).remove();
    }
  });

}

//Add event to already generated HTML 
$("#hashtag_list").on("click", "button", removeTag); 


//Create the websocket to the location host
var ws = new WebSocket('ws://' + window.location.host + '/ws');

//Compile the template
var source = $("#gram-template").html();
var template = Handlebars.compile(source);

//Save the #main element since it will be accessed frequently
var main = $("#main");

//Create a queue of new posts to add to the page every second.
var gram_queue = []

ws.onmessage = function(ev) {

  //Parse the JSON received from the server
  var json = JSON.parse(ev.data);

  //Preload the image
  var i = new Image();
  i.src = json.new_val.images.low_resolution.url;

  //Render the template
  var html = template(json);

  gram_queue.push(html);
};

window.setInterval(function() {

  if (gram_queue.length > 0) {

    if (main.find(".row:first").children().length == 3) {
      main.prepend("<div class='row'></div>");
    }

    //Get the front item off the gram queue
    var rendered_gram = gram_queue.shift();

    //Append the new gram
    var new_gram = main.find(".row:first").append(rendered_gram);

    //Fade it in
    new_gram.find(".gram:last").transition({
      "opacity": 100
    });

    //Clean up the list
    var rows = $("#main .row");
    if (rows.length > 8) {
      console.log("Cleaning up rows you cannot see!");
      rows.slice(8).remove();
    }
  }
}, 600);

ws.onerror = function(ev) {
  console.log(ev)
  console.log("A socket error has occurred!")
};