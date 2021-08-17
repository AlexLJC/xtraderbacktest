// Load the backtest result
function load(backtest_result,file_name){
    candle_chart_holder = document.getElementById("candle_chart_holder");
    candle_chart_holder.innerHTML = "";
    var chart = LightweightCharts.createChart(candle_chart_holder, 
        { 
            width: candle_chart_holder.offsetWidth,
            height: window.innerHeight/2 ,
            timeScale: {
                timeVisible: true,
                borderColor: '#D1D4DC',
            },
            rightPriceScale: {
                borderColor: '#D1D4DC',
            },
            layout: {
                backgroundColor: '#ffffff',
                textColor: '#000',
            },
            grid: {
                horzLines: {
                    color: '#F0F3FA',
                },
                vertLines: {
                    color: '#F0F3FA',
                },
            },
            
        } 
       
        
    );
    chart.applyOptions({
        watermark: {
            color: 'rgba(11, 94, 29, 0.4)',
            visible: true,
            text: 'Backtest Evaluation ' + file_name,
            fontSize: 24,
            horzAlign: 'left',
            vertAlign: 'bottom',
        },
    });
    
    
    for(var symbol in backtest_result["price_data"]){
        var candlestickSeries = chart.addCandlestickSeries(
            {
                upColor: 'rgb(38,166,154)',
                downColor: 'rgb(255,82,82)',
                wickUpColor: 'rgb(38,166,154)',
                wickDownColor: 'rgb(255,82,82)',
                borderVisible: false,
          }
        );
        data_list = [];
        for(var bar_index in backtest_result["price_data"][symbol]){
            bar = backtest_result["price_data"][symbol][bar_index];
            data_list.push({ time: bar["timestamp"], open: bar["open"], high: bar["high"], low: bar["low"], close: bar["close"]});
        }
        // set data
        candlestickSeries.setData(data_list);
        // load the order for it
        var markers_orders = [];
        for(var position_index in backtest_result["positions"]){
            position = backtest_result["positions"][position_index];
            if(position["symbol"] == symbol){
                if(position["direction"] == "long"){
                    markers_orders.push({ time: position["open_timestamp"], position: 'belowBar', color: '#2196F3', shape: 'arrowUp', text: 'Long@ ' + position["open_filled_price"]});
                    markers_orders.push({ time: position["close_timestamp"], position: 'aboveBar', color: '#e91e63', shape: 'arrowDown', text: 'Short@ ' + position["close_filled_price"]});
                }
                else if (position["direction"] == "short"){
                    markers_orders.push({ time: position["open_timestamp"], position: 'aboveBar', color: '#e91e63', shape: 'arrowDown', text: 'Short@ ' + position["open_filled_price"]});
                    markers_orders.push({ time: position["close_timestamp"], position: 'belowBar', color: '#2196F3', shape: 'arrowUp', text: 'Long@ ' + position["close_filled_price"]});
                }
            }
            
        }
        candlestickSeries.setMarkers(markers_orders);
    }
    
    document.getElementById("win_rate").innerHTML = Math.floor(backtest_result["summary"]["win_rate"] * 100).toString(10) + '<sup style="font-size: 20px">%</sup>';
    document.getElementById("long_win_rate").innerHTML = Math.floor(backtest_result["summary"]["long_win_rates"] * 100).toString(10) + '<sup style="font-size: 20px">%</sup>';
    document.getElementById("short_win_rate").innerHTML = Math.floor(backtest_result["summary"]["short_win_rates"] * 100).toString(10) + '<sup style="font-size: 20px">%</sup>';
    document.getElementById("profit_drawdown").innerHTML = Math.floor(backtest_result["summary"]["profit/max_draw_down"] * 100).toString(10) + '<sup style="font-size: 20px">%</sup>';
    document.getElementById("total_trades").innerHTML = backtest_result["summary"]["total_trades"];
    document.getElementById("long_trades").innerHTML = backtest_result["summary"]["total_long_trades"];
    document.getElementById("short_trades").innerHTML = backtest_result["summary"]["total_short_trades"];
    document.getElementById("total_orders").innerHTML = backtest_result["orders"].length;
    document.getElementById("total_profits").innerHTML = backtest_result["summary"]["total_profit"].toFixed(2);
    document.getElementById("long_profits").innerHTML = backtest_result["summary"]["total_long_profit"].toFixed(2);
    document.getElementById("short_profits").innerHTML = backtest_result["summary"]["total_short_profit"].toFixed(2);
    document.getElementById("avg_profit").innerHTML = backtest_result["summary"]["avg_profit"].toFixed(2);
    document.getElementById("avg_win").innerHTML = backtest_result["summary"]["avg_win"].toFixed(2);
    document.getElementById("avg_loss").innerHTML = backtest_result["summary"]["avg_loss"].toFixed(2);
    document.getElementById("avg_win_avg_loss").innerHTML = backtest_result["summary"]["avg_win/avg_loss"].toFixed(2);
    document.getElementById("max_win").innerHTML = backtest_result["summary"]["max_profit"].toFixed(2);
    document.getElementById("max_loss").innerHTML = backtest_result["summary"]["max_loss"].toFixed(2);
    document.getElementById("max_rise_up").innerHTML = backtest_result["summary"]["overall_max_rise_up"].toFixed(2);
    document.getElementById("max_draw_down").innerHTML = backtest_result["summary"]["max_draw_down"].toFixed(2);
    order_table = document.getElementById("example1");
    // Clear tab;e
    var row_count = order_table.rows.length;
    for (var i = 1; i < row_count; i++) {
        order_table.deleteRow(1);
    }
    var i = 0;
    for(var order in backtest_result["orders"]){
        var row = order_table.insertRow(i);
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        var cell3 = row.insertCell(2);
        var cell4 = row.insertCell(3);
        var cell5 = row.insertCell(4);
        var cell6 = row.insertCell(5);
        var cell7 = row.insertCell(6);
        cell1.innerHTML = "order" + i;
        i++;
    }
}

// Import file
function importFile(){
    var selectedFile = document.getElementById("files").files[0];
    var name = selectedFile.name;
    var size = selectedFile.size;
    console.log("Loading File Name " +name+" File Size " + size + " bytes");

    var reader = new FileReader();
    reader.readAsText(selectedFile);

    reader.onload = function(){
        var backtest_result = JSON.parse(this.result);
        console.log("File content in json.");
        console.log(backtest_result);
        load(backtest_result,name);
    };
}