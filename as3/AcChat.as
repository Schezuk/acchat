// Class used to communicate with AcChat Server
// PORT = 1818

package org.tamaki.net
{
	import com.adobe.serialization.json.JSON;
	
	import flash.display.Loader;
	import flash.events.EventDispatcher;
	
	import org.tamaki.comment.CommentData;
	import org.tamaki.events.*;
	
	public class AcChat extends EventDispatcher
	{
		private var mysock:MySocket;
		public var partid:Number;
		
		public function AcChat(host:String="www.avfun001.org",port:uint=1818,channel:Number=1000.001)
		{
			mysock = new MySocket(host,port);
			mysock.addEventListener(LoadEvent.SUB_RECEIVED,onReceived);
			mysock.addEventListener(LoadEvent.SOCKET_CONNECTED,onConnected);
			this.partid = channel;
		}
		
		public function onReceived(eve:LoadEvent):void{
			var str:String = eve.info as String;
			try{
				var j:Object = JSON.decode(str);
				if (j.ok || j.error)
					return
				var cd:CommentData = new CommentData(j.mode,j.time,j.color,j.fontsize,j.txt,j.date,true);
				this.dispatchEvent(new CommentEvent(CommentEvent.CMT_UPDATE,cd));
			}catch(e:Error){
				// do nothing
			}
		}
		
		public function onConnected(eve:LoadEvent):void{
			this.joinChannel(this.partid);
		}
		
		public function joinChannel(partid:Number):void{
			var msg:Object = new Object();
			msg.protocol = "partid";
			msg.partid = partid;
			var str:String = JSON.encode(msg)+"\n";
			send(str);
		}
		
		public function sendCmt(cmt:CommentData):void{
			var msg:Object = new Object();
			msg.protocol = "leavemsg";
			msg.txt = cmt.txt;
			msg.color = cmt.color;
			msg.date = cmt.date;
			msg.fontsize = cmt.fontSize;
			msg.mode = cmt.mode;
			msg.time = cmt.time;
			msg.partid = this.partid;
			var str:String = JSON.encode(msg)+"\n";
			send(str);
		}
		
		public function send(str:String):void{
			mysock.send(str);
		}
	}
}
