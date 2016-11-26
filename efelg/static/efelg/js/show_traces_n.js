function TEST() {




$.getJSON('/efelg/get_data/rat_hippocampus_CA1_IN_cAC_OLM-980205FHP_98205022', function(data) {
    var cell_obj = JSON.parse(data)
    var test = TracePlot('charts', cell_obj)
    })
}

const SHOW_FADED = 0.15
const SHOW_CHECK = 0.65
const SHOW_HOVER = 1.0

function TracePlot(container_id, cell_obj) {
    var n_traces = Object.keys(cell_obj['traces']).length
    var self = this

    this.container = $('#' + container_id)
    this.cell_obj = cell_obj
    
    this.appearance = new Array(n_traces)
    this.appearance.fill(SHOW_FADED)
    
    this.tmp_appearance_hover = null
        
    function init() {
        var md5 = cell_obj['md5']
        var timestamp = Date.now()
        
        self.cellinfo = [self.cell_obj['species'], self.cell_obj['area'],
                         self.cell_obj['region'], self.cell_obj['type'],
                         self.cell_obj['etype'], self.cell_obj['name'],
                         self.cell_obj['sample']]
    
        // Erase everything
        self.container.empty()
        
        // Creates the boxes that will host info and data
        
        self.infobox = $('<div/>', {
            'id': 'info_' + md5 + timestamp,
            'class': 'panel-heading fn-container',
        }).appendTo(self.container)
        
        self.formbox = $('<div/>', {
            'id': 'form_' + md5 + timestamp,
            'class': 'hidden',
        }).appendTo(self.container)
        
        self.plotbox = $('<div/>', {
            'id': 'plot_' + md5 + timestamp,
        }).appendTo(self.container)

        // Populates the boxes

        self.infobox.append('<span></span>').text('Cell properties: ' + self.cellinfo.join(' -> '))
        self.infobox.append('<br><br>')
        self.infobox.append('<button class="selall btn btn-link btn-default">Select all</button>')
        self.infobox.append('<button class="dselall btn btn-link btn-default">Deselect all</button>')
        self.infobox.append('<button class="invsel btn btn-default btn-link">Invert selection</button>')
    }

	function manageLegend() {
		var legend = Plotly.d3.select('#' + self.plotbox.attr('id') + ' g.legend')
		var elems = legend.selectAll('.traces rect')

		// Saves the value of the opacity before the mousehover
		function savePrevious(d) {
		    var i = d[0].trace.index

		    self.tmp_appearance_hover = self.appearance[i]

		    self.appearance[i] = SHOW_HOVER

		    self.refresh()
		}

		// Restores the value of the opacity after the mouseleave
		function restorePrevious(d) {
		    var i = d[0].trace.index

		    self.appearance[i] = self.tmp_appearance_hover

		    self.refresh()
		}

		// Allows to toggle the opacity of the specified trace
		function setOpacity(d) {
		    var check_name = 'input[name^="' + d[0].trace.name.slice(0, -3) + '"]'

		    if (self.tmp_appearance_hover == SHOW_FADED) {
		        self.formbox.find(check_name)[0].checked = true
		        self.tmp_appearance_hover = SHOW_CHECK
	        } else {
		        self.formbox.find(check_name)[0].checked = false
		        self.tmp_appearance_hover = SHOW_FADED
		    }
		}

		// Binds the events to every element of the legend
		elems.each(function() {
		    Plotly.d3.select(this).on('click', setOpacity)
		    Plotly.d3.select(this).on('mouseenter', savePrevious)
		    Plotly.d3.select(this).on('mouseleave', restorePrevious)
		})

	}

    function plot() {
        var plotdata = []
        $.each(self.cell_obj['traces'], function(key, trace) {
            self.formbox.append('<input type="checkbox" name="' + key + '" />')

            // Defines what is about to be plotted
            var newTrace = {
                y: trace,
                name: key + ' ' + self.cell_obj['amp_unit'],
                mode: 'lines',
                hoverinfo: 'none',
                opacity: SHOW_FADED
            }
            plotdata.push(newTrace)
        })

        // Sorts the traces names (mathematical order)
        plotdata.sort(function(a, b) {
            var a = parseFloat(a.name)
            var b = parseFloat(b.name)

            if (a == b) {
                return 0	
            } else if (a < b) {
                return 1
            } else {
                return -1
            }                     
        })

        var layout = {
            legend: {
                orientation: "h",
                x: 0,
                y: 1.2,
            },
            margin: {l: 40, b: 60, t: 0} 
        }

        Plotly.newPlot(self.plotbox.attr('id'), plotdata, layout, {displayModeBar: false}).then(manageLegend)
        self.refresh()
    }
    
    function bindEvents() {
		self.plotbox.on('plotly_relayout', function(ev) {
			self.refresh()
		})


		// Select every trace
		self.infobox.find('.selall').click(function(ev) {
			self.appearance.fill(SHOW_CHECK)
			self.formbox.find('input').prop('checked', true)

			self.refresh()
		})

		// Deselect all traces
		self.infobox.find('.dselall').click(function(ev) {
			self.appearance.fill(SHOW_FADED)
			self.formbox.find('input').prop('checked', false)

			self.refresh()
		})

		// Invers the selection
		self.infobox.find('.invsel').click(function(ev) {
			for (var i = 0; i < self.appearance.length; i++) {
				self.appearance[i] = self.appearance[i] == SHOW_FADED ? SHOW_CHECK : SHOW_FADED

				var cb = self.formbox.find('input')[i]
				cb.checked = ! cb.checked
			}

			self.refresh()
		})
    }
    
    this.refresh = function() {
        var update = {
            opacity: self.appearance
        }

        Plotly.restyle(self.plotbox.attr('id'), update).then(manageLegend)

        // Sets the opacities of the legend's labels
        legend = Plotly.d3.select('#' + self.plotbox.attr('id') + ' g.legend')
        legend.selectAll('.traces').each(function(d, i) {
            Plotly.d3.select(this).style('opacity', update.opacity[i] + 0.4)
        })
    }
    
    init()
    plot()
    bindEvents()
}

