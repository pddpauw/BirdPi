<?php 
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

$db = new SQLite3('./scripts/birds.db', SQLITE3_OPEN_CREATE | SQLITE3_OPEN_READWRITE);
if($db == False){
  echo "Database is busy";
  header("refresh: 0;");
}
?>

<script>
function login(elem){
	document.getElementById("error").innerHTML = "";
	setTimeout(function () {
		if(document.getElementById("username").value != "" && document.getElementById("password").value != "") {
			const request = new XMLHttpRequest();
			request.open('GET', "views.php?view=Tools", false, document.getElementById("username").value,document.getElementById("password").value)
			request.onreadystatechange = function() {
			   	if(request.readyState === 4 && request.status === 200) {
			       document.location.href = "views.php?view=Tools";
			    } else {
			    	document.getElementById("error").innerHTML = "Invalid Credentials";
			    }
			   
			}
			request.send()
		} else {
			document.getElementById("error").innerHTML = "Invalid Credentials";
		}
		elem.classList.remove('disabled');
	}, 1000)
}
</script>

<div class="settings">
	<table class="settingstable" style="margin-left: auto;margin-right: auto;"><tr><td>
		<h2 style="text-align: center">Login</h2>
		<p id="error"></p>
		<div style="line-height:32px">
		    <label for="username">Username: </label>
		    <input id="username" name="username" type="text" required/><br>
		    <label for="password" style="margin-top:5px;padding-right:3px;">Password: </label>
		    <input id="password" name="password" type="password" required/><br>
		    <button style="background:#9fe29b" type="button" id="basicformsubmit" onclick="this.classList.add('disabled');login(this);" name="view" value="Login">Submit</button>

		</div>
	</td></tr></table>
</div>