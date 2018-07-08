/* Javascript for videojsXBlock. */
function videojsXBlockInitView(runtime, element) {
    /* Weird behaviour :
     * In the LMS, element is the DOM container.
     * In the CMS, element is the jQuery object associated*
     * So here I make sure element is the jQuery object */
    if(element.innerHTML) element = $(element);
    
    var video = element.find('video:first');
    var player = videojs(video.get(0), {playbackRates:[0.75,1,1.25,1.5,1.75,2]}, function() {});
    
    player.qualityselector({
        sources: [
          { format: 'highres', src: 'http://www.sample-videos.com/video/mp4/720/big_buck_bunny_720p_1mb.mp4', type: 'video/mp4'},
          { format: 'hd1080', src: 'http://www.sample-videos.com/video/mp4/720/big_buck_bunny_720p_1mb.mp4', type: 'video/mp4'},
          { format: 'hd720', src: 'http://www.sample-videos.com/video/mp4/480/big_buck_bunny_480p_1mb.mp4', type: 'video/mp4'},
          { format: 'large', src: '//vjs.zencdn.net/v/oceans.mp4', type: 'video/mp4'},
          { format: 'medium', src: 'http://www.sample-videos.com/video/mp4/480/big_buck_bunny_480p_1mb.mp4', type: 'video/mp4'},
          { format: 'small', src: 'http://www.sample-videos.com/video/mp4/480/big_buck_bunny_480p_1mb.mp4', type: 'video/mp4'},
          { format: 'auto', src: 'http://www.sample-videos.com/video/mp4/720/big_buck_bunny_720p_1mb.mp4', type: 'video/mp4'}
        ],
        formats: [
          { code: 'highres', name: 'High' },
          { code: 'hd1080', name: '1080p' },
          { code: 'hd720', name: '720p' },
          { code: 'large', name: '480p' },
          { code: 'medium', name: '360p' },
          { code: 'small', name: '240p' },
          { code: 'auto', name: 'Auto' }
        ],

        onFormatSelected: function(format) {
          console.log(format);
        }
      });

}
