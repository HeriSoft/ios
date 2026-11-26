package com.herisoft.caloriescan

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.DirectionsRun
import androidx.compose.material.icons.automirrored.filled.MenuBook
import androidx.compose.material.icons.filled.MonitorWeight
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.Restaurant
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.herisoft.caloriescan.core.DemoData
import com.herisoft.caloriescan.ui.BodyScreen
import com.herisoft.caloriescan.ui.CalorieTheme
import com.herisoft.caloriescan.ui.ConditionScreen
import com.herisoft.caloriescan.ui.ExerciseScreen
import com.herisoft.caloriescan.ui.FoodScreen
import com.herisoft.caloriescan.ui.HomeMoveScreen
import com.herisoft.caloriescan.ui.HomeWorkoutScreen
import com.herisoft.caloriescan.ui.LabelScanScreen
import com.herisoft.caloriescan.ui.LogScreen
import com.herisoft.caloriescan.ui.LookupScreen
import com.herisoft.caloriescan.ui.ManualProductScreen
import com.herisoft.caloriescan.ui.PlanScreen
import com.herisoft.caloriescan.ui.ProductScreen
import com.herisoft.caloriescan.ui.ScanScreen
import com.herisoft.caloriescan.ui.ScannedTextScreen
import com.herisoft.caloriescan.ui.SymptomInputScreen
import com.herisoft.caloriescan.ui.SymptomResultScreen

private data class Tab(val route: String, val title: String, val icon: ImageVector)

private val tabs = listOf(
    Tab("scan", "Quét", Icons.Filled.QrCodeScanner),
    Tab("food", "Món ăn", Icons.Filled.Restaurant),
    Tab("exercise", "Tập luyện", Icons.AutoMirrored.Filled.DirectionsRun),
    Tab("body", "Cơ thể", Icons.Filled.MonitorWeight),
    Tab("log", "Nhật ký", Icons.AutoMirrored.Filled.MenuBook),
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        // Chế độ demo dùng trên CI: adb shell am start ... --es demoScreen log
        val demoScreen = intent.getStringExtra("demoScreen")
        setContent {
            CalorieTheme { App(demoScreen) }
        }
    }
}

@Composable
private fun App(demoScreen: String?) {
    val vm: AppViewModel = viewModel()
    val nav = rememberNavController()
    val backStack by nav.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route
    var currentTab by rememberSaveable { mutableStateOf("scan") }

    LaunchedEffect(demoScreen) {
        if (demoScreen != null) currentTab = openDemo(demoScreen, vm, nav)
    }

    Scaffold(
        bottomBar = {
            NavigationBar {
                tabs.forEach { tab ->
                    NavigationBarItem(
                        selected = currentTab == tab.route,
                        onClick = {
                            currentTab = tab.route
                            nav.navigate(tab.route) {
                                popUpTo(nav.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(tab.icon, contentDescription = null) },
                        label = { Text(tab.title, maxLines = 1) },
                    )
                }
            }
        },
    ) { padding ->
        NavHost(nav, startDestination = "scan", modifier = Modifier.padding(padding)) {
            composable("scan") { ScanScreen(vm, nav, active = currentRoute == "scan") }
            composable("lookup/{code}", arguments = listOf(navArgument("code") { type = NavType.StringType })) {
                LookupScreen(vm, nav, it.arguments?.getString("code") ?: "")
            }
            composable("product") { ProductScreen(vm, nav) }
            composable("text") { ScannedTextScreen(vm, nav) }
            composable("label?code={code}", arguments = listOf(navArgument("code") { type = NavType.StringType; nullable = true })) {
                LabelScanScreen(vm, nav, it.arguments?.getString("code"))
            }
            composable("manual?code={code}", arguments = listOf(navArgument("code") { type = NavType.StringType; nullable = true })) {
                ManualProductScreen(vm, nav, it.arguments?.getString("code"))
            }
            composable("food") { FoodScreen(vm, nav) }
            composable("exercise") { ExerciseScreen(vm, nav) }
            composable("plan") { PlanScreen(vm, nav) }
            composable("homeWorkout") { HomeWorkoutScreen(nav) }
            composable("move/{id}") { HomeMoveScreen(nav, it.arguments?.getString("id") ?: "") }
            composable("body") { BodyScreen(vm, nav) }
            composable("symptoms") { SymptomInputScreen(vm, nav) }
            composable("symptomResult") { SymptomResultScreen(vm, nav) }
            composable("condition/{id}/{med}") {
                ConditionScreen(nav, it.arguments?.getString("id") ?: "", it.arguments?.getString("med") == "1")
            }
            composable("log") { LogScreen(vm) }
        }
    }
}

/** Mở màn hình demo, trả về tab cần chọn. */
private fun openDemo(screen: String, vm: AppViewModel, nav: NavHostController): String {
    vm.seedDemo(withLog = screen == "log" || screen == "exercise")
    when (screen) {
        "detail" -> { vm.selectProduct(DemoData.sampleProduct); nav.navigate("product") }
        "label" -> { vm.demoLabelLines = DemoData.labelLines; nav.navigate("label") }
        "food" -> { vm.demoFoodGuesses = DemoData.foodGuesses(); nav.navigate("food") }
        "exercise" -> nav.navigate("exercise")
        "plan" -> { nav.navigate("exercise"); nav.navigate("plan") }
        "body" -> nav.navigate("body")
        "symptoms" -> {
            vm.symptomInput = DemoData.symptomInput
            nav.navigate("body"); nav.navigate("symptoms"); nav.navigate("symptomResult")
        }
        "log" -> nav.navigate("log")
    }
    return when (screen) {
        "food" -> "food"
        "exercise", "plan" -> "exercise"
        "body", "symptoms" -> "body"
        "log" -> "log"
        else -> "scan"
    }
}
